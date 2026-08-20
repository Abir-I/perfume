/* THE LAST NOTE — Admin CRUD controller
 * Restores the original admin dashboard's working Add / Edit / Delete flow.
 * Premium-only form fields remain visual helpers; only fields backed by the
 * existing schema are submitted to the API, so no fake data is persisted.
 */
const API_BASE = '/api';
let allProducts = [];
let brandsCache = [];
let editingPerfumeId = null;
let selectedImageFile = null;
let pendingDeleteProductId = null;

function adminToken() {
  return localStorage.getItem('access_token') || localStorage.getItem('token') || '';
}

function showToast(message, type='success') {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div'); el.id='toast'; el.className='admin-toast';
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.dataset.type = type;
  el.classList.add('show');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => el.classList.remove('show'), 3000);
}

async function adminFetch(url, options={}) {
  const token = adminToken();
  const headers = {...(options.headers || {})};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(url, {...options, headers});
  if (res.status === 401 || res.status === 403) {
    showToast('Admin authorization failed. Please log in again.', 'error');
    throw new Error('Not authorized');
  }
  return res;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function imageUrl(url) {
  if (!url) return '';
  if (/^https?:\/\//i.test(url) || url.startsWith('/')) return url;
  return '/' + url.replace(/^\/+/, '');
}

function debounce(fn, ms=300) {
  let timer; return (...args) => { clearTimeout(timer); timer=setTimeout(()=>fn(...args),ms); };
}

async function loadBrandsIntoForm() {
  const select=document.getElementById('fBrand');
  if (!select) return;
  try {
    const res=await fetch(`${API_BASE}/catalog/brands/`);
    const data=await res.json();
    brandsCache=data.results || data || [];
    select.innerHTML='<option value="">Select a brand…</option>' + brandsCache.map(b=>
      `<option value="${escapeHtml(b.brand_id)}">${escapeHtml(b.brand_name)}</option>`).join('');
  } catch(e) { showToast('Could not load brands.', 'error'); }
}

function stockBadge(stock) {
  const n=Number(stock||0);
  if(n<=0) return '<span class="stock-badge out-of-stock">Out of stock</span>';
  if(n<=5) return `<span class="stock-badge low-stock">${n} left</span>`;
  return `<span class="stock-badge in-stock">${n} in stock</span>`;
}

function featureBadges(p) {
  const badges=[];
  if (p.is_active === false || p.is_active === 0) badges.push('<span class="feature-badge">Inactive</span>');
  return badges.length ? badges.join(' ') : '<span class="feature-badge">Standard</span>';
}

function filteredProducts() {
  const search=(document.getElementById('adminSearchInput')?.value||'').trim().toLowerCase();
  const brand=document.getElementById('filterBrand')?.value||'';
  const gender=document.getElementById('filterGender')?.value||'';
  const type=(document.getElementById('filterType')?.value||'').toLowerCase();
  const status=document.getElementById('filterStatus')?.value||'';
  return allProducts.filter(p=>{
    const hay=[p.perfume_name,p.brand_name,p.concentration,p.product_type,p.target_gender].join(' ').toLowerCase();
    if(search && !hay.includes(search)) return false;
    if(brand && String(p.brand_id)!==String(brand)) return false;
    if(gender && String(p.target_gender)!==gender) return false;
    if(type && String(p.product_type).toLowerCase()!==type) return false;
    const stock=Number(p.stock_quantity||0);
    if(status==='in_stock' && stock<=0) return false;
    if(status==='out_of_stock' && stock>0) return false;
    if(status==='low_stock' && (stock<=0 || stock>5)) return false;
    return true;
  });
}

async function loadProducts() {
  const body=document.getElementById('adminTableBody');
  if(body) body.innerHTML='<tr><td colspan="9" class="admin-loading">Loading products…</td></tr>';
  try {
    const res=await adminFetch(`${API_BASE}/catalog/admin/products/`);
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||'Could not load products');
    allProducts=data.results||[];
    const count=document.getElementById('adminCount'); if(count) count.textContent=`${allProducts.length} products`;
    renderProducts(filteredProducts());
  } catch(e) {
    if(body) body.innerHTML='<tr><td colspan="9" class="admin-empty">Couldn’t load products. Check login/API/database.</td></tr>';
  }
}

function renderProducts(products) {
  const body=document.getElementById('adminTableBody');
  const cards=document.getElementById('adminCardsWrapper');
  if(!body) return;
  if(!products.length) {
    body.innerHTML='<tr><td colspan="9" class="admin-empty">No products found.</td></tr>';
    if(cards) cards.innerHTML='<div class="admin-empty">No products found.</div>';
    return;
  }
  body.innerHTML=products.map(p=>{
    const img=imageUrl(p.image_url);
    const image=img ? `<img class="admin-row-thumb" src="${escapeHtml(img)}" alt="" onerror="this.style.display='none'">` : `<div class="admin-row-thumb admin-no-image">${escapeHtml((p.perfume_name||'?').slice(0,1).toUpperCase())}</div>`;
    return `<tr>
      <td>${image}</td>
      <td><div class="admin-row-name">${escapeHtml(p.perfume_name)}</div></td>
      <td><span class="admin-row-brand">${escapeHtml(p.brand_name||'')}</span></td>
      <td>৳${Number(p.price||0).toLocaleString()}</td>
      <td>—</td>
      <td>${stockBadge(p.stock_quantity)}</td>
      <td>${Number(p.stock_quantity||0)>0 ? '<span class="feature-badge active">Active</span>' : '<span class="feature-badge">Out of stock</span>'}</td>
      <td>${featureBadges(p)}</td>
      <td><div class="admin-row-actions">
        <button type="button" class="admin-icon-btn" title="Edit" data-action="edit" data-perfume-id="${p.perfume_id}" data-product-id="${p.product_id}">✎ Edit</button>
        <button type="button" class="admin-icon-btn delete-btn" title="Delete product variant" data-action="delete" data-product-id="${p.product_id}" data-name="${escapeHtml(p.perfume_name)}">🗑 Delete</button>
      </div></td>
    </tr>`;
  }).join('');
  if(cards) cards.innerHTML=products.map(p=>`<div class="admin-product-card"><div class="admin-product-card-body"><div class="admin-product-card-top"><div><div class="admin-row-name">${escapeHtml(p.perfume_name)}</div><div class="admin-row-brand">${escapeHtml(p.brand_name||'')}</div></div><div>৳${Number(p.price||0).toLocaleString()}</div></div><div class="admin-product-card-meta">${escapeHtml(p.concentration||'')} · ${escapeHtml(p.product_type||'')} · ${Number(p.volume_ml||0)}ml</div>${stockBadge(p.stock_quantity)}<div class="admin-product-card-actions"><button type="button" class="admin-icon-btn" data-action="edit" data-perfume-id="${p.perfume_id}" data-product-id="${p.product_id}">✎ Edit</button><button type="button" class="admin-icon-btn delete-btn" data-action="delete" data-product-id="${p.product_id}" data-name="${escapeHtml(p.perfume_name)}">🗑 Delete</button></div></div></div>`).join('');
}

function resetForm() {
  const form=document.getElementById('perfumeForm'); if(form) form.reset();
  selectedImageFile=null;
  const preview=document.getElementById('imagePreview'); if(preview){preview.src='';preview.style.display='none';}
  const txt=document.getElementById('imageUploadText'); if(txt) txt.textContent='📤 Drag & drop or click to upload';
  const err=document.getElementById('perfumeFormError'); if(err){err.classList.remove('show');err.textContent='';}
  const file=document.getElementById('imageFileInput'); if(file) file.value='';
}

async function openPerfumeModal(perfumeId=null, productId=null) {
  editingPerfumeId=perfumeId ? Number(perfumeId) : null;
  resetForm();
  const title=document.getElementById('perfumeModalTitle'); if(title) title.textContent=editingPerfumeId?'Edit Perfume':'Add New Perfume';
  const form=document.getElementById('perfumeForm'); if(form) form.dataset.productId=productId||'';
  if(editingPerfumeId) {
    const p=allProducts.find(x=>Number(x.product_id)===Number(productId));
    if(p) {
      const set=(id,v)=>{const e=document.getElementById(id);if(e&&v!==undefined&&v!==null)e.value=v;};
      set('fBrand',p.brand_id); set('fName',p.perfume_name); set('fConcentration',p.concentration); set('fGender',p.target_gender);
      set('fProductType',p.product_type); set('fVolume',p.volume_ml); set('fPrice',p.price); set('fStock',p.stock_quantity);
      const img=imageUrl(p.image_url); if(img){const pr=document.getElementById('imagePreview');if(pr){pr.src=img;pr.style.display='block';} const t=document.getElementById('imageUploadText');if(t)t.textContent='Click to replace image';}
    }
    try {
      const res=await fetch(`${API_BASE}/catalog/perfumes/${editingPerfumeId}/`); const data=await res.json(); const d=data.perfume||data;
      const set=(id,v)=>{const e=document.getElementById(id);if(e&&v!==undefined&&v!==null)e.value=v;};
      set('fBrand',d.brand_id);set('fName',d.perfume_name);set('fConcentration',d.concentration);set('fGender',d.target_gender);set('fLongevity',d.longevity_hours);set('fSeason',d.recommended_season);set('fTopNotes',d.top_notes);set('fMiddleNotes',d.middle_notes);set('fBaseNotes',d.base_notes);set('fDescription',d.description);
    } catch(e) {}
  }
  document.getElementById('perfumeModalOverlay')?.classList.add('open');
}

function closePerfumeModal(){document.getElementById('perfumeModalOverlay')?.classList.remove('open');editingPerfumeId=null;}

function handleImageSelect(e){
  const file=e.target.files?.[0]; if(!file)return;
  if(file.size>5*1024*1024){showToast('Image must be 5 MB or smaller.','error');e.target.value='';return;}
  if(!file.type.startsWith('image/')){showToast('Please select an image file.','error');e.target.value='';return;}
  selectedImageFile=file; const r=new FileReader(); r.onload=ev=>{const p=document.getElementById('imagePreview');if(p){p.src=ev.target.result;p.style.display='block';}const t=document.getElementById('imageUploadText');if(t)t.textContent=file.name;};r.readAsDataURL(file);
}

async function submitPerfumeForm(e){
  e.preventDefault();
  const err=document.getElementById('perfumeFormError'); const setErr=m=>{if(err){err.textContent=m;err.classList.add('show');}};
  if(err)err.classList.remove('show');
  const required=['fBrand','fName','fConcentration','fGender','fProductType','fVolume','fPrice'];
  for(const id of required){const el=document.getElementById(id);if(!el?.value){setErr('Please fill in every required field.');el?.focus();return;}}
  if(Number(document.getElementById('fPrice').value)<=0){setErr('Price must be greater than 0.');return;}
  if(Number(document.getElementById('fVolume').value)<=0){setErr('Volume must be greater than 0.');return;}
  if(Number(document.getElementById('fStock').value||0)<0){setErr('Stock cannot be negative.');return;}
  const fd=new FormData();
  const map={fBrand:'brand_id',fName:'perfume_name',fConcentration:'concentration',fGender:'target_gender',fLongevity:'longevity_hours',fSeason:'recommended_season',fTopNotes:'top_notes',fMiddleNotes:'middle_notes',fBaseNotes:'base_notes',fDescription:'description',fProductType:'product_type',fVolume:'volume_ml',fPrice:'price',fStock:'stock_quantity'};
  Object.entries(map).forEach(([id,key])=>fd.append(key,document.getElementById(id)?.value||''));
  if(selectedImageFile) fd.append('image',selectedImageFile);
  const productId=document.getElementById('perfumeForm')?.dataset.productId; if(editingPerfumeId&&productId)fd.append('product_id',productId);
  const btn=document.getElementById('perfumeFormSubmitBtn'); if(btn){btn.disabled=true;btn.textContent='Saving…';}
  try{
    const url=editingPerfumeId?`${API_BASE}/catalog/admin/perfumes/${editingPerfumeId}/`:`${API_BASE}/catalog/admin/perfumes/`;
    const res=await adminFetch(url,{method:editingPerfumeId?'PATCH':'POST',body:fd}); const data=await res.json();
    if(!res.ok){const first=data.errors?Object.values(data.errors)[0]:data.error||'Unable to save perfume.';setErr(first);return;}
    showToast(editingPerfumeId?'Perfume updated successfully.':'Perfume added successfully.'); closePerfumeModal(); await loadProducts();
  }catch(ex){setErr(ex.message==='Not authorized'?'Admin authorization failed.':'Network/server error. Check Django console.');}
  finally{if(btn){btn.disabled=false;btn.textContent='Save Perfume';}}
}

function openDeleteConfirm(productId,name){pendingDeleteProductId=Number(productId);document.getElementById('deleteConfirmText').textContent=`Remove the product variant “${name}”? Existing orders are protected; the API will deactivate instead of breaking order history when necessary.`;document.getElementById('deleteConfirmOverlay')?.classList.add('open');}
function closeDeleteConfirm(){document.getElementById('deleteConfirmOverlay')?.classList.remove('open');pendingDeleteProductId=null;}
async function confirmDelete(){if(!pendingDeleteProductId)return;const btn=document.getElementById('deleteConfirmActionBtn');if(btn){btn.disabled=true;btn.textContent='Deleting…';}try{const res=await adminFetch(`${API_BASE}/catalog/admin/products/${pendingDeleteProductId}/`,{method:'DELETE'});const data=await res.json();if(!res.ok)throw new Error(data.error||'Delete failed');showToast(data.message||'Product deleted.');closeDeleteConfirm();await loadProducts();}catch(e){showToast(e.message,'error');}finally{if(btn){btn.disabled=false;btn.textContent='Delete';}}}

function bindDashboard(){
  document.getElementById('addPerfumeBtn')?.addEventListener('click',()=>openPerfumeModal());
  document.getElementById('perfumeForm')?.addEventListener('submit',submitPerfumeForm);
  document.getElementById('perfumeFormCancelBtn')?.addEventListener('click',closePerfumeModal);
  document.getElementById('deleteConfirmCancelBtn')?.addEventListener('click',closeDeleteConfirm);
  document.getElementById('deleteConfirmActionBtn')?.addEventListener('click',confirmDelete);
  document.getElementById('deleteConfirmOverlay')?.addEventListener('click',e=>{if(e.target.id==='deleteConfirmOverlay')closeDeleteConfirm();});
  document.getElementById('perfumeModalOverlay')?.addEventListener('click',e=>{if(e.target.id==='perfumeModalOverlay')closePerfumeModal();});
  document.getElementById('imageFileInput')?.addEventListener('change',handleImageSelect);
  document.getElementById('imageUploadZone')?.addEventListener('click',()=>document.getElementById('imageFileInput')?.click());
  document.getElementById('logoutBtn')?.addEventListener('click',()=>{localStorage.removeItem('access_token');localStorage.removeItem('token');localStorage.removeItem('user');window.location.href='/';});
  document.getElementById('adminSearchInput')?.addEventListener('input',debounce(()=>renderProducts(filteredProducts())));
  ['filterBrand','filterGender','filterType','filterStatus','filterFeature'].forEach(id=>document.getElementById(id)?.addEventListener('change',()=>renderProducts(filteredProducts())));
  document.getElementById('resetFiltersBtn')?.addEventListener('click',()=>{['adminSearchInput','filterBrand','filterGender','filterType','filterStatus','filterFeature'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});renderProducts(allProducts);});
  document.getElementById('adminTableBody')?.addEventListener('click',e=>{const b=e.target.closest('button[data-action]');if(!b)return;if(b.dataset.action==='edit')openPerfumeModal(b.dataset.perfumeId,b.dataset.productId);if(b.dataset.action==='delete')openDeleteConfirm(b.dataset.productId,b.dataset.name);});
  document.getElementById('adminCardsWrapper')?.addEventListener('click',e=>{const b=e.target.closest('button[data-action]');if(!b)return;if(b.dataset.action==='edit')openPerfumeModal(b.dataset.perfumeId,b.dataset.productId);if(b.dataset.action==='delete')openDeleteConfirm(b.dataset.productId,b.dataset.name);});
}

document.addEventListener('DOMContentLoaded',async()=>{bindDashboard();await loadBrandsIntoForm();await loadProducts();});
