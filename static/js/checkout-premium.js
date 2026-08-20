(() => {
  'use strict';

  const token = localStorage.getItem('access_token');
  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const money = (value) => `৳${Number(value || 0).toLocaleString('en-BD', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
  let selectedAddressId = null;
  let addresses = [];

  const authHeaders = () => ({
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json'
  });

  function showError(message) {
    const box = $('checkoutAlert');
    box.textContent = message;
    box.classList.add('show');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function clearError() {
    $('checkoutAlert').classList.remove('show');
    $('checkoutAlert').textContent = '';
  }

  function applyAddress(address) {
    if (!address) return;
    $('address').value = address.line1 || '';
    $('city').value = address.city || '';
    $('state').value = address.state || '';
    $('postalCode').value = address.postal_code || '';
    $('country').value = address.country || 'Bangladesh';
  }

  async function loadProfile() {
    const response = await fetch('/api/accounts/profile/', { headers: authHeaders() });
    if (!response.ok) return;
    const data = await response.json();
    $('name').value = data.name || `${data.first_name || ''} ${data.last_name || ''}`.trim();
    $('email').value = data.email || '';
    $('phone').value = data.phone || '';
  }

  async function loadAddresses() {
    const box = $('savedAddresses');
    const response = await fetch('/api/accounts/addresses/', { headers: authHeaders() });
    if (!response.ok) {
      box.innerHTML = '<div class="co-empty">No saved address found. Enter your delivery address below.</div>';
      return;
    }
    const data = await response.json();
    addresses = Array.isArray(data.addresses) ? data.addresses : [];
    if (!addresses.length) {
      box.innerHTML = '<div class="co-empty">No saved address found. Enter your delivery address below.</div>';
      return;
    }
    box.innerHTML = addresses.map((a, index) => `
      <label>
        <input type="radio" name="savedAddress" value="${esc(a.address_id)}" ${a.default || index === 0 ? 'checked' : ''}>
        <strong>${esc(a.label || 'Saved address')}</strong><br>
        ${esc(a.line1 || '')}, ${esc(a.city || '')}${a.state ? `, ${esc(a.state)}` : ''} ${esc(a.postal_code || '')}
      </label>
    `).join('');

    const checked = box.querySelector('input:checked');
    if (checked) {
      selectedAddressId = checked.value;
      applyAddress(addresses.find(a => String(a.address_id) === String(selectedAddressId)));
    }
    box.querySelectorAll('input[name="savedAddress"]').forEach((input) => {
      input.addEventListener('change', () => {
        selectedAddressId = input.value;
        applyAddress(addresses.find(a => String(a.address_id) === String(input.value)));
        clearError();
      });
    });
  }

  function fallbackBottle() {
    return '<span class="co-bottle" aria-hidden="true"></span>';
  }

  async function loadCart() {
    const response = await fetch('/api/cart/', { headers: authHeaders() });
    if (!response.ok) throw new Error(response.status === 401 ? 'Please log in before checkout.' : 'Could not load your cart.');
    const data = await response.json();
    if (!data.items?.length) throw new Error('Your cart is empty.');

    const items = data.items;
    $('cartCount').textContent = data.total_items || items.reduce((sum, item) => sum + Number(item.quantity || 0), 0);
    $('orderItems').innerHTML = items.map((item) => {
      const image = item.image || item.image_url;
      const media = image ? `<img src="${esc(image)}" alt="${esc(item.product_name)}">` : fallbackBottle();
      return `
        <div class="co-item">
          <div class="co-item-img">${media}</div>
          <div>
            <div class="co-item-name">${esc(item.product_name)}</div>
            <div class="co-item-meta">${esc(item.brand || 'Premium Collection')} · ${esc(item.volume_ml)}ml × ${esc(item.quantity)}</div>
          </div>
          <div class="co-item-price">${money(item.subtotal)}</div>
        </div>
      `;
    }).join('');
    $('orderItems').querySelectorAll('img').forEach((img) => {
      img.addEventListener('error', () => { img.parentElement.innerHTML = fallbackBottle(); }, { once: true });
    });

    const subtotal = Number(data.subtotal ?? data.total_price ?? 0);
    const shipping = Number(data.shipping ?? 0);
    const total = Number(data.total_price ?? subtotal + shipping);
    $('subtotal').textContent = money(subtotal);
    $('shipping').textContent = shipping ? money(shipping) : 'Free';
    $('total').textContent = money(total);
  }

  function validate() {
    const name = $('name').value.trim();
    const email = $('email').value.trim();
    const phone = $('phone').value.trim();
    const address = $('address').value.trim();
    const city = $('city').value.trim();
    const country = $('country').value.trim();
    if (!name) return 'Please enter your full name.';
    if (!email) return 'Please enter your email address.';
    if (!phone) return 'Please enter your phone number.';
    if (!selectedAddressId && (!address || !city || !country)) return 'Please select a saved address or complete the delivery address.';
    return null;
  }

  function showSuccess(orderNumber, total) {
    $('successOrder').textContent = orderNumber ? `Order ${orderNumber}` : 'Your order has been confirmed';
    $('successTotal').textContent = total ? `Total ${money(total)}` : 'Thank you for shopping with The Last Note.';
    $('successOverlay').classList.add('show');
    document.body.style.overflow = 'hidden';
    window.setTimeout(() => { window.location.href = '/'; }, 2200);
  }

  async function submitOrder(event) {
    event.preventDefault();
    clearError();
    const validationError = validate();
    if (validationError) { showError(validationError); return; }

    const button = $('submitBtn');
    button.disabled = true;
    button.classList.add('loading');

    const payload = {
      name: $('name').value.trim(),
      email: $('email').value.trim(),
      phone: $('phone').value.trim(),
      payment_method: 'cod',
      notes: ''
    };

    if (selectedAddressId) {
      payload.address_id = Number(selectedAddressId);
    } else {
      payload.address = $('address').value.trim();
      payload.city = $('city').value.trim();
      payload.state = $('state').value.trim();
      payload.postal_code = $('postalCode').value.trim();
      payload.country = $('country').value.trim();
    }

    try {
      const response = await fetch('/api/orders/checkout/', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'We could not place your order. Please try again.');
      showSuccess(data.order_number, data.total_amount);
    } catch (error) {
      showError(error.message);
      button.disabled = false;
      button.classList.remove('loading');
    }
  }

  function bind() {
    if (!token) { window.location.href = '/'; return; }
    $('checkoutForm').addEventListener('submit', submitOrder);
    ['address','city','state','postalCode','country'].forEach((id) => {
      $(id).addEventListener('input', () => {
        selectedAddressId = null;
        document.querySelectorAll('input[name="savedAddress"]').forEach((radio) => { radio.checked = false; });
        clearError();
      });
    });
    Promise.all([loadProfile(), loadAddresses(), loadCart()]).catch((error) => showError(error.message));
  }

  document.addEventListener('DOMContentLoaded', bind);
})();
