

'use strict';

/* ── CONFIG ── */
const API_BASE = '/api';
let cartItems  = 0;
let chatIsOpen = false;


const KB = {
  platform: `The Last Note is a web-based perfume retail platform that sells authentic
    perfumes in smaller fractional units called decants (5ml, 10ml, 20ml) as well as
    full bottles. The business purchases original perfumes in bulk from authorized
    retailers and sells smaller portions so customers can try premium fragrances
    before committing to a full bottle. Every decant is linked to its source bottle
    for complete authenticity traceability.`,

  decants: `A decant is a smaller portion carefully poured from an original sealed perfume bottle.
    Sizes available:
    • 5ml — The Sampler: 30-50 wears, from ৳250. Perfect for discovering new scents.
    • 10ml — The Tester: 60-100 wears, from ৳480. A proper trial across seasons.
    • 20ml — Extended trial, from ৳900.
    • Full Bottle — The original sealed bottle, from ৳5,000.
    Every decant is linked to its source bottle's batch number so you can verify exactly
    what you're wearing.`,

  process: `Our decanting process in 3 steps:
    Step 1 — Authentic Sourcing: We buy sealed bottles exclusively from authorized
    brand retailers. Each is photographed, batch-coded, and entered into our
    traceability system before any seal is broken.
    Step 2 — Precision Decanting: Specialists fill medical-grade glass atomizers to
    exact weight. Each decant is labeled with its source bottle's batch number.
    Step 3 — Sealed & Traced: Your order includes a traceability card with the original
    bottle details, pour date, and your decant's sequence number.`,

  authenticity: `Every bottle is purchased from authorized retailers only. Each bottle is:
    • Photographed and documented before opening
    • Assigned a unique batch number
    • Marked as authenticity-verified in our system
    • Linked to every decant poured from it
    Customers can view the batch number on any product page and verify their
    decant traces back to a specific, authenticated original bottle.`,

  products: [
    { name:'Sauvage', brand:'Dior', concentration:'EDP', top:'Bergamot, Pepper',
      mid:'Lavender, Star Anise', base:'Ambroxan, Cedar', longevity:'8 hours',
      sillage:'Strong', season:'All Season', gender:'Male', price5:'350', price10:'650',
      notes:'One of our best-sellers. Fresh, spicy, magnetic. Works year-round.' },
    { name:'Black Orchid', brand:'Tom Ford', concentration:'EDP', top:'Black Truffle, Ylang',
      mid:'Black Orchid, Jasmine', base:'Sandalwood, Vanilla', longevity:'7 hours',
      sillage:'Strong', season:'Winter', gender:'Unisex', price5:'450', price10:'800',
      notes:'Dark, luxurious, sensual. Perfect for evenings and special occasions.' },
    { name:'Aventus', brand:'Creed', concentration:'EDP', top:'Blackcurrant, Apple',
      mid:'Jasmine, Rose', base:'Musk, Oakmoss', longevity:'9 hours',
      sillage:'Enormous', season:'All Season', gender:'Male', price5:'600', price10:'1100',
      notes:'A legendary fragrance with exceptional longevity and projection.' },
    { name:'Eros', brand:'Versace', concentration:'EDT', top:'Lemon, Apple, Mint',
      mid:'Tonka Bean, Geranium', base:'Vanilla, Vetiver', longevity:'6 hours',
      sillage:'Moderate', season:'Spring', gender:'Male', price5:'280', price10:'520',
      notes:'Fresh, vibrant, and youthful. Great for daytime and casual wear.' },
    { name:'Acqua di Gio', brand:'Armani', concentration:'EDT', top:'Calabrian Bergamot',
      mid:'Jasmine, Rosemary', base:'Patchouli, White Musk', longevity:'5 hours',
      sillage:'Moderate', season:'Summer', gender:'Male', price5:'250', price10:'480',
      notes:'Our most affordable luxury. Fresh, aquatic, and office-friendly.' },
  ],

  shipping: `We deliver within Dhaka in 1–3 business days after order confirmation.
    Every order ships with a traceability card.
    Returns: Unopened, unused items can be returned within 3 days of delivery.
    Opened decants cannot be returned for hygiene reasons.`,

  payment: `We currently accept Cash on Delivery. Payment is collected when your order is delivered.`,

  faq: [
    { triggers: ['what is a decant','explain decant','decant meaning'],
      response: `A decant is a smaller portion poured from an original full perfume bottle. Instead of buying a 100ml bottle you haven't tried, you can start with 5ml, 10ml, or 20ml. Every decant at The Last Note is poured from a sealed, authenticated bottle and carries the source bottle's batch number so you can verify its origin.` },

    { triggers: ['how do you verify','are they real','is it authentic','original perfume','fake'],
      response: `Every bottle is purchased from authorized brand retailers only. Before any seal is broken, we photograph the bottle, assign a unique batch number, and log it in our traceability system. Each decant is then labeled with that batch number — so you can always trace exactly which bottle your fragrance came from. We also maintain an authenticity-verified flag for every bottle in our database.` },

    { triggers: ['shipping','delivery','how long','when will i receive','how many days'],
      response: `We deliver within Dhaka in 1–3 business days after your order is confirmed. Your order ships with a traceability card showing the source bottle details and your decant's sequence number.` },

    { triggers: ['return','refund','exchange','send back'],
      response: `Unopened, unused items can be returned within 3 days of delivery — just contact us with your order number. Opened decants cannot be returned for hygiene reasons, which is why we recommend trying a 5ml sample first!` },

    { triggers: ['payment','pay','bkash','nagad','card','cash'],
      response: `We currently accept Cash on Delivery. Payment is collected when your order is delivered.` },

    { triggers: ['track order','where is my order','order status','tracking'],
      response: `Log into your account and go to My Orders to track your order in real-time. Status goes: Pending → Confirmed → Processing → Shipped → Delivered. You can also use the "Track Order" link in the navigation bar.` },

    { triggers: ['account','sign up','register','create account'],
      response: `Click the person icon (👤) in the top-right corner to create an account or log in. Having an account lets you track orders, save multiple shipping addresses, submit reviews, and get personalized AI recommendations.` },

    { triggers: ['price','cost','how much','cheap','expensive','affordable'],
      response: `Our 5ml decants start from ৳250 (Acqua di Gio), 10ml from ৳480. Our most premium fragrance, Creed Aventus, is ৳600 for 5ml — still a fraction of the full bottle price. This is the whole point of decanting: luxury fragrances at accessible prices.` },

    { triggers: ['review','rating','leave feedback','write review'],
      response: `Verified customers (those who have purchased the product) can leave 1-5 star ratings and written reviews on any product page. We display all verified reviews to help other customers make confident decisions.` },

    { triggers: ['5ml','sampler','try'],
      response: `Our 5ml size — The Sampler — gives you 30-50 wears, enough to properly experience a fragrance across different moods and temperatures. Starting from ৳250, it's the lowest-risk way to explore premium perfumery.` },
  ]
};


function buildResponse(input) {
  const msg  = input.toLowerCase().trim();
  const prods = KB.products;

  /* --- FAQ match --- */
  for (const item of KB.faq) {
    if (item.triggers.some(t => msg.includes(t))) return item.response;
  }

  
  for (const p of prods) {
    if (msg.includes(p.name.toLowerCase()) || msg.includes(p.brand.toLowerCase())) {
      return `${p.brand} ${p.name} ${p.concentration}\n\n🌿 Top: ${p.top}\n🌸 Heart: ${p.mid}\n🌳 Base: ${p.base}\n\n⏱ Longevity: ${p.longevity} · Sillage: ${p.sillage}\n📅 Season: ${p.season} · For: ${p.gender}\n\n💰 From ৳${p.price5} (5ml) · ৳${p.price10} (10ml)\n\n${p.notes}`;
    }
  }

  /* --- Season recommendations --- */
  if (/(summer|hot weather|warm season|spring summer)/.test(msg)) {
    const picks = prods.filter(p => ['Summer','Spring','All Season'].includes(p.season));
    return `For warm weather, I'd recommend:\n\n${picks.map(p=>`• ${p.brand} ${p.name} — ${p.top.split(',')[0]} notes, from ৳${p.price5}`).join('\n')}\n\nAll available as 5ml samples so you can try before committing. Which sounds interesting?`;
  }
  if (/(winter|cold|christmas|festive)/.test(msg)) {
    const picks = prods.filter(p => ['Winter','All Season'].includes(p.season));
    return `For cold weather and evenings, I'd suggest:\n\n${picks.map(p=>`• ${p.brand} ${p.name} — ${p.top.split(',')[0]} notes, from ৳${p.price5}`).join('\n')}\n\nRich, warm fragrances for the season. Want details on any of these?`;
  }

  /* --- Occasion recommendations --- */
  if (/(office|work|professional|daytime|day wear)/.test(msg)) {
    const picks = prods.filter(p => p.sillage === 'Moderate');
    return `For the office, I'd suggest moderate sillage fragrances that won't overwhelm colleagues:\n\n${picks.map(p=>`• ${p.brand} ${p.name} — ${p.sillage} sillage, ৳${p.price5} for 5ml`).join('\n')}\n\nModerate projection, long enough to last the day without being overpowering.`;
  }
  if (/(date|evening|night out|dinner|romantic|special occasion)/.test(msg)) {
    const picks = prods.filter(p => ['Strong','Enormous'].includes(p.sillage));
    return `For a date night or special occasion, you want something that leaves an impression:\n\n${picks.map(p=>`• ${p.brand} ${p.name} — ${p.sillage} sillage, ৳${p.price5} for 5ml`).join('\n')}\n\nBold, confident, memorable. Try a 5ml first to make sure it works on your skin.`;
  }

  /* --- Gender --- */
  if (/(for her|for women|female|feminine|girlfriend|wife|mother)/.test(msg)) {
    const picks = prods.filter(p => p.gender === 'Female' || p.gender === 'Unisex');
    return `For women, I'd recommend:\n\n${picks.map(p=>`• ${p.brand} ${p.name} (${p.gender}) — ৳${p.price5} for 5ml\n  ${p.notes}`).join('\n\n')}\n\nAll available in sample sizes. Would you like to know more about any of these?`;
  }
  if (/(for him|for men|male|masculine|boyfriend|husband|father)/.test(msg)) {
    const picks = prods.filter(p => p.gender === 'Male' || p.gender === 'Unisex');
    return `Great choices for men:\n\n${picks.slice(0,3).map(p=>`• ${p.brand} ${p.name} — ৳${p.price5} for 5ml\n  ${p.notes}`).join('\n\n')}\n\nWould you like recommendations based on a specific season or occasion?`;
  }

  /* --- Budget --- */
  if (/(cheap|budget|affordable|least expensive|under 300|under 500|cheapest)/.test(msg)) {
    const picks = [...prods].sort((a,b) => parseInt(a.price5)-parseInt(b.price5)).slice(0,3);
    return `Our most affordable 5ml decants:\n\n${picks.map(p=>`• ${p.brand} ${p.name} — ৳${p.price5}`).join('\n')}\n\nAll are 100% authentic, batch-traced from sealed bottles. The price reflects the decant size, not quality compromises.`;
  }

  /* --- Long lasting --- */
  if (/(long lasting|longevity|all day|strongest|lasts longest|best sillage|projection)/.test(msg)) {
    const picks = [...prods].sort((a,b) => parseFloat(b.longevity)-parseFloat(a.longevity)).slice(0,3);
    return `Our longest-lasting fragrances:\n\n${picks.map(p=>`• ${p.brand} ${p.name} — ${p.longevity}, ${p.sillage} sillage, ৳${p.price5}`).join('\n')}\n\nCreed Aventus is our most tenacious — enormous projection and 9+ hours easily.`;
  }

  /* --- Best sellers / recommendations --- */
  if (/(best seller|popular|most loved|recommended|your favourite|what should i try|where do i start)/.test(msg)) {
    return `Our most popular fragrances right now:\n\n⭐ Dior Sauvage EDP — The all-rounder. From ৳350.\n⭐ Creed Aventus — The legend. From ৳600.\n⭐ Armani Acqua di Gio — Best value. From ৳250.\n\nAll available in 5ml samples. I'd suggest starting with Sauvage if you're unsure — it works on almost everyone.`;
  }

  /* --- Greetings --- */
  if (/^(hi|hello|hey|good morning|good evening|good afternoon|salaam|assalam|হ্যালো)/.test(msg)) {
    const opts = [
      `Hello! Welcome to The Last Note. 🌸 I'm here to help you find your next signature scent. What are you looking for — a specific perfume, a recommendation by season, or something else?`,
      `Hi there! I'm Nota, your AI fragrance guide. Ask me about any perfume in our collection, or tell me an occasion or season and I'll suggest something perfect.`,
      `Welcome! I can help you discover the right fragrance for any occasion, budget, or season. What would you like to explore today?`
    ];
    return opts[Math.floor(Math.random() * opts.length)];
  }

  /* --- Thanks --- */
  if (/(thank|thanks|great help|helpful|perfect|exactly what)/.test(msg)) {
    return `You're very welcome! 🌸 If you'd like to explore more fragrances or have any questions, I'm always here. Enjoy your next scent from The Last Note.`;
  }

  /* --- About the platform --- */
  if (/(about you|about the last note|who are you|what is this|what do you sell)/.test(msg)) {
    return KB.platform + '\n\nWe make luxury fragrances accessible by letting you try before you commit.';
  }

  /* --- Default --- */
  return `I'm not sure I understood that perfectly — try asking me about:\n\n• A specific perfume (Sauvage, Aventus, Black Orchid…)\n• Recommendations by season, occasion, or budget\n• How our decanting works\n• Shipping, returns, and payment\n• Authenticity and traceability\n\nWhat would you like to know? 🌸`;
}

/* ── API call → local fallback ── */
async function getAIResponse(message) {
  try {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/chatbot/ask/`, {
      method: 'POST', headers,
      body: JSON.stringify({ message }),
      signal: AbortSignal.timeout(4000)
    });
    if (res.ok) {
      const data = await res.json();
      const text = data.response || data.reply || data.message;
      if (text) return text;
    }
  } catch { /* fall through to local */ }

  await delay(650 + Math.random() * 400); /* realistic thinking pause */
  return buildResponse(message);
}

/* ══════════════════════════════════════════════════════════════
   CHATBOT UI
   ══════════════════════════════════════════════════════════════ */
function openChat() {
  chatIsOpen = true;
  const panel = document.getElementById('chatPanel');
  panel.classList.add('visible');
  requestAnimationFrame(() => panel.classList.add('open'));
  document.getElementById('fabChatIcon').style.display  = 'none';
  document.getElementById('fabCloseIcon').style.display = 'block';
  document.getElementById('chatInput').focus();
}

function closeChat() {
  chatIsOpen = false;
  const panel = document.getElementById('chatPanel');
  panel.classList.remove('open');
  setTimeout(() => panel.classList.remove('visible'), 350);
  document.getElementById('fabChatIcon').style.display  = 'block';
  document.getElementById('fabCloseIcon').style.display = 'none';
}

// Chatbot only exists on the homepage — guard so other pages
// (shop, cart, checkout, admin) that share this same script.js
// don't crash here and lose the navbar/search code below it.
document.getElementById('chatFab')?.addEventListener('click', () => {
  chatIsOpen ? closeChat() : openChat();
});

document.getElementById('chatForm')?.addEventListener('submit', e => {
  e.preventDefault();
  dispatchMessage();
});

async function dispatchMessage() {
  const input = document.getElementById('chatInput');
  const text  = input.value.trim();
  if (!text) return;
  input.value = '';

  addMsg(text, 'user');

  /* typing indicator */
  const typing = document.createElement('div');
  typing.className = 'typing-dots'; typing.id = 'typing';
  typing.innerHTML = '<span></span><span></span><span></span>';
  document.getElementById('chatMessages').appendChild(typing);
  scrollChat();

  const reply = await getAIResponse(text);
  document.getElementById('typing')?.remove();
  addMsg(reply, 'bot');
}

function sendSuggestion(btn, text) {
  /* remove suggestion chips after first use */
  document.getElementById('chatSuggestions')?.remove();
  document.getElementById('chatInput').value = text;
  dispatchMessage();
}

function addMsg(text, role) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = text.replace(/\n/g, '<br/>');
  document.getElementById('chatMessages').appendChild(div);
  scrollChat();
}

function scrollChat() {
  const m = document.getElementById('chatMessages');
  m.scrollTop = m.scrollHeight;
}

/* ══════════════════════════════════════════════════════════════
   PRODUCTS
   ══════════════════════════════════════════════════════════════ */
const FALLBACK_PRODUCTS = [
  { perfume_name:'Sauvage', brand_name:'Dior', top_notes:'Bergamot · Pepper · Cedar', price:'350', badge:'BEST SELLER', badge_class:'badge-dark',
    img:'https://images.unsplash.com/photo-1599305090598-fe179d501227?w=500&q=80&auto=format' },
  { perfume_name:'Aventus', brand_name:'Creed', top_notes:'Blackcurrant · Birch · Ambergris', price:'600', badge:'TOP RATED', badge_class:'badge-brass',
    img:'https://images.unsplash.com/photo-1595425970377-c9703cf48b6d?w=500&q=80&auto=format' },
  { perfume_name:'Black Orchid', brand_name:'Tom Ford', top_notes:'Black Truffle · Orchid · Vanilla', price:'450', badge_class:'',
    img:'https://images.unsplash.com/photo-1541643600914-78b084683702?w=500&q=80&auto=format' },
  { perfume_name:'Acqua di Gio', brand_name:'Armani', top_notes:'Bergamot · Jasmine · White Musk', price:'250', badge:'NEW', badge_class:'badge-sage',
    img:'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=500&q=80&auto=format' },
];

async function loadProducts() {
  try {
    const res  = await fetch(`${API_BASE}/catalog/products/`, { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    const list = (data.results || data).slice(0, 4);
    renderProducts(list);
    const count = data.count || list.length;
    const statEl = document.getElementById('stat-frag');
    if (statEl) statEl.textContent = count + '+';
  } catch {
    renderProducts(FALLBACK_PRODUCTS);
  }
}

const FALLBACK_IMG = 'https://images.unsplash.com/photo-1541643600914-78b084683702?w=500&q=80&auto=format';

function renderProducts(list) {
  const grid = document.getElementById('productGrid');
  if (!grid) return; // featured products grid only exists on the homepage
  grid.innerHTML = list.map((p, i) => {
    const badgeClass = p.badge_class || (p.badge === 'BEST SELLER' ? 'badge-dark' : p.badge === 'TOP RATED' ? 'badge-brass' : p.badge === 'NEW' ? 'badge-sage' : '');
    const price5  = Number(p.price || 0);
    const price10 = Math.round(price5 * 1.85);
    const priceFull = Math.round(price5 * 22);
    return `
    <article class="product-card reveal-up ${i > 0 ? `delay-${i}` : ''}" data-product-id="${p.product_id || ''}" data-perfume-name="${p.perfume_name}" data-brand-name="${p.brand_name || p.brand || ''}">
      <div class="product-card-img">
        <img
          src="${p.img || p.image_url || FALLBACK_IMG}"
          alt="${p.perfume_name}"
          loading="lazy"
          onerror="this.src='${FALLBACK_IMG}'"
        />
        ${p.badge ? `<span class="product-badge ${badgeClass}">${p.badge}</span>` : ''}
        <button class="quick-view-overlay" onclick="quickView('${p.perfume_name}', '${p.brand_name || ''}', '${p.product_id || ''}')">
          View Details
        </button>
      </div>
      <div class="product-card-body">
        <p class="product-brand">${p.brand_name || p.brand || ''}</p>
        <p class="product-name">${p.perfume_name}</p>
        <p class="product-notes">${p.top_notes || ''}</p>
        <div class="size-btns" data-prices="${price5},${price10},${priceFull}">
          <button class="size-btn on" onclick="selectSize(this)">5ML</button>
          <button class="size-btn" onclick="selectSize(this)">10ML</button>
          <button class="size-btn" onclick="selectSize(this)">FULL</button>
        </div>
        <p class="product-price" data-price="${price5}">৳${price5.toLocaleString()}</p>
        <button class="add-btn" data-no-nav onclick="addToCart(this, '${p.perfume_name}', '${p.product_id || ''}')">Add to Cart</button>
      </div>
    </article>`;
  }).join('');

  /* observe new cards */
  grid.querySelectorAll('.reveal-up').forEach(el => revealObserver.observe(el));
}

function selectSize(btn) {
  const wrap   = btn.closest('.size-btns');
  const prices = wrap.dataset.prices.split(',').map(Number);
  const idx    = [...wrap.children].indexOf(btn);
  wrap.querySelectorAll('.size-btn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  const priceEl = wrap.closest('.product-card-body').querySelector('.product-price');
  priceEl.textContent = '৳' + prices[idx].toLocaleString();
  priceEl.dataset.price = prices[idx];
}

function addToCart(btn, name, productId) {
  /* Real AJAX add-to-cart when we know the product; optimistic UI otherwise. */
  if (productId && window.TLN) {
    window.TLN.addToCart(productId, 1)
      .then(data => showToast(`${name} added to cart (${data.total_items} items)`))
      .catch(err => showToast(err.message || 'Could not add to cart'));
  } else {
    cartItems++;
    document.getElementById('cartBadge').textContent = cartItems;
    showToast(`${name} added to cart`);
  }
  btn.textContent = '✓ Added';
  btn.classList.add('added');
  setTimeout(() => {
    btn.textContent = 'Add to Cart';
    btn.classList.remove('added');
  }, 2000);
}

function quickView(name, brand) {
  showToast(`Quick view — ${brand} ${name} · coming soon`);
}

/* ══════════════════════════════════════════════════════════════
   REVIEWS CAROUSEL
   ══════════════════════════════════════════════════════════════ */
const REVIEWS = [
  { text: 'The Creed Aventus decant was indistinguishable from the bottle I tried at the counter. The traceability card was a nice touch — really builds trust.', name: 'Rafi Islam', product: 'Creed Aventus · 10ml', rating: 5, avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&q=80' },
  { text: 'Finally found a way to try Dior Sauvage without committing to the full price. The 5ml lasted me weeks and the quality was absolutely the real thing.', name: 'Nadia Sultana', product: 'Dior Sauvage EDP · 5ml', rating: 5, avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&q=80' },
  { text: 'Ordered three different 5ml samples before deciding on Aventus. This is exactly how fragrance shopping should work. Delivery was quick too.', name: 'Tanvir Ahmed', product: 'Multiple 5ml Samples', rating: 5, avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&q=80' },
  { text: 'Tom Ford Black Orchid is incredible and I never would have known without trying a decant first. Bought the full bottle two weeks later.', name: 'Sumaiya Hossain', product: 'Tom Ford Black Orchid · 5ml → Full Bottle', rating: 5, avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&q=80' },
  { text: 'The packaging was elegant and the fragrance arrived perfectly sealed. The batch traceability gave me complete confidence it was authentic.', name: 'Karim Uddin', product: 'Versace Eros EDT · 10ml', rating: 4, avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=80&q=80' },
  { text: 'Excellent service. Acqua di Gio 5ml is a steal at that price. Have already recommended The Last Note to five friends.', name: 'Farhana Begum', product: 'Armani Acqua di Gio · 5ml', rating: 5, avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=80&q=80' },
];

let revIdx = 0;
const VISIBLE_REVIEWS = () => window.innerWidth < 640 ? 1 : window.innerWidth < 900 ? 2 : 3;

function renderReviews() {
  const track = document.getElementById('reviewsTrack');
  const dots  = document.getElementById('reviewsDots');
  if (!track || !dots) return; // reviews carousel only exists on the homepage

  track.innerHTML = REVIEWS.map(r => `
    <div class="review-card">
      <div class="review-stars">
        ${[1,2,3,4,5].map(n => `<div class="star${n > r.rating ? ' empty' : ''}"></div>`).join('')}
      </div>
      <p class="review-text">"${r.text}"</p>
      <div class="review-meta">
        <div class="reviewer-avatar">
          <img src="${r.avatar}" alt="${r.name}" loading="lazy"/>
        </div>
        <div>
          <p class="reviewer-name">${r.name}</p>
          <p class="reviewer-product">${r.product}</p>
        </div>
      </div>
    </div>
  `).join('');

  const pageCount = Math.ceil(REVIEWS.length / VISIBLE_REVIEWS());
  dots.innerHTML = Array.from({length: pageCount}, (_,i) => `
    <button class="dot-btn${i===0?' on':''}" aria-label="Review page ${i+1}" onclick="goReview(${i})"></button>
  `).join('');
}

function goReview(idx) {
  const vis   = VISIBLE_REVIEWS();
  const total = Math.ceil(REVIEWS.length / vis);
  revIdx = Math.max(0, Math.min(idx, total - 1));
  const cardW = document.querySelector('.review-card')?.offsetWidth || 0;
  const gap   = 24;
  document.getElementById('reviewsTrack').style.transform =
    `translateX(-${revIdx * vis * (cardW + gap)}px)`;
  document.querySelectorAll('.dot-btn').forEach((d, i) => d.classList.toggle('on', i === revIdx));
}

document.getElementById('revPrev')?.addEventListener('click', () => goReview(revIdx - 1));
document.getElementById('revNext')?.addEventListener('click', () => goReview(revIdx + 1));

/* ══════════════════════════════════════════════════════════════
   SEARCH
   ══════════════════════════════════════════════════════════════ */
let searchTimer;
const searchTrigger  = document.getElementById('searchTrigger');
const searchDropdown = document.getElementById('searchDropdown');
const searchInput    = document.getElementById('searchInput');
const searchCloseBtn = document.getElementById('searchCloseBtn');

function closeSearchDropdown() {
  searchDropdown.classList.remove('open');
  searchDropdown.setAttribute('aria-hidden', 'true');
  if (window.innerWidth <= 640) document.body.style.overflow = '';
}

searchTrigger.addEventListener('click', () => {
  const open = searchDropdown.classList.toggle('open');
  searchDropdown.setAttribute('aria-hidden', String(!open));
  if (open) {
    searchInput.focus();
    // On mobile the dropdown becomes a fixed full-width panel, so lock
    // background scroll the same way the mobile nav/cart drawer already do.
    if (window.innerWidth <= 640) document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

searchCloseBtn.addEventListener('click', closeSearchDropdown);

document.addEventListener('click', e => {
  if (!e.target.closest('.nav-search-wrap')) {
    closeSearchDropdown();
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeSearchDropdown();
});

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(runSearch, 280);
});

async function runSearch() {
  const q = searchInput.value.trim();
  const resultsEl = document.getElementById('searchResults');
  if (!q || q.length < 2) { resultsEl.innerHTML = ''; return; }

  /* local search first */
  const local = FALLBACK_PRODUCTS.filter(p =>
    p.perfume_name.toLowerCase().includes(q.toLowerCase()) ||
    (p.brand_name || '').toLowerCase().includes(q.toLowerCase())
  );

  /* try API */
  let results = local;
  try {
    const res  = await fetch(`${API_BASE}/catalog/products/?search=${encodeURIComponent(q)}`, { signal: AbortSignal.timeout(3000) });
    const data = await res.json();
    const api  = (data.results || data).slice(0, 5);
    if (api.length) results = api;
  } catch { /* use local */ }

  if (!results.length) {
    resultsEl.innerHTML = '<p class="search-empty">No fragrances found. Try a brand name or scent family.</p>';
    return;
  }
resultsEl.innerHTML = results.map((p, idx) => `
    <div class="search-result-row" role="option" tabindex="0" data-index="${idx}" data-product-id="${p.product_id || ''}" data-perfume-name="${p.perfume_name}" data-brand-name="${p.brand_name || p.brand || ''}">
      <div class="sr-info">
        <span class="sr-brand">${p.brand_name || p.brand || ''}</span>
        <span class="sr-name">${p.perfume_name}</span>
      </div>
      <span class="sr-price">From ৳${Number(p.price||0).toLocaleString()}</span>
    </div>
  `).join('');

  // Add click handler to search results
  document.querySelectorAll('.search-result-row').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function() {
      const perfumeName = this.getAttribute('data-perfume-name');
      const brandName = this.getAttribute('data-brand-name');
      const productId = this.getAttribute('data-product-id');

      // Close search dropdown
      closeSearchDropdown();

      // Open the dynamic Product Details page
      quickView(perfumeName, brandName, productId);
    });
  });
}

/* ══════════════════════════════════════════════════════════════
   NAVBAR SCROLL BEHAVIOR
   ══════════════════════════════════════════════════════════════ */
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('solid', window.scrollY > 60);
  updateActiveLink();
}, { passive: true });

function updateActiveLink() {
  const anchors = ['shop','decants','brands','how'];
  let current = '';
  anchors.forEach(id => {
    const el = document.getElementById(id);
    if (el && window.scrollY >= el.offsetTop - 100) current = id;
  });
  document.querySelectorAll('.nav-link[data-section]').forEach(l => {
    l.classList.toggle('active', l.dataset.section === current);
  });
  document.querySelectorAll('.mobile-nav-link[data-section]').forEach(l => {
    l.classList.toggle('active', l.dataset.section === current);
  });
}

/* ══════════════════════════════════════════════════════════════
   MOBILE HAMBURGER MENU
   ══════════════════════════════════════════════════════════════ */
const navHamburger = document.getElementById('navHamburger');
const mobileNavPanel = document.getElementById('mobileNavPanel');
const mobileNavOverlay = document.getElementById('mobileNavOverlay');

function toggleMobileNav(forceOpen) {
  const shouldOpen = forceOpen ?? !mobileNavPanel.classList.contains('open');
  navHamburger.classList.toggle('open', shouldOpen);
  navHamburger.setAttribute('aria-expanded', String(shouldOpen));
  mobileNavPanel.classList.toggle('open', shouldOpen);
  mobileNavPanel.setAttribute('aria-hidden', String(!shouldOpen));
  mobileNavOverlay.classList.toggle('open', shouldOpen);
  document.body.style.overflow = shouldOpen ? 'hidden' : '';
}

navHamburger.addEventListener('click', () => toggleMobileNav());
mobileNavOverlay.addEventListener('click', () => toggleMobileNav(false));

// Tapping any link inside the mobile menu should close it, so people
// aren't left staring at the menu after they've already navigated.
document.querySelectorAll('.mobile-nav-link').forEach(link => {
  link.addEventListener('click', () => toggleMobileNav(false));
});

// Escape key closes it too, same as the cart drawer / modals
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') toggleMobileNav(false);
});

// If someone resizes back to desktop width with the menu open, close it
// so it can't get stuck open behind the (now-hidden) hamburger button.
window.addEventListener('resize', () => {
  if (window.innerWidth > 640) toggleMobileNav(false);
});

/* ══════════════════════════════════════════════════════════════
   SCROLL REVEAL
   ══════════════════════════════════════════════════════════════ */
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('in');
      revealObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.10 });

document.querySelectorAll('.reveal-up').forEach(el => revealObserver.observe(el));

/* ══════════════════════════════════════════════════════════════
   HERO PARALLAX  (subtle — only the image shifts)
   ══════════════════════════════════════════════════════════════ */
const heroImg = document.getElementById('heroImg');
let ticking   = false;

window.addEventListener('scroll', () => {
  if (!ticking && heroImg) {
    window.requestAnimationFrame(() => {
      const scrolled = window.scrollY;
      heroImg.style.transform = `translateY(${scrolled * 0.18}px)`;
      ticking = false;
    });
    ticking = true;
  }
}, { passive: true });

/* ══════════════════════════════════════════════════════════════
   BRAND TICKER — load real brands from API
   ══════════════════════════════════════════════════════════════ */
async function loadBrands() {
  try {
    const res    = await fetch(`${API_BASE}/catalog/brands/`, { signal: AbortSignal.timeout(3000) });
    const data = await res.json();
    const brands = data.results || data;
    if (brands && brands.length) {
      const doubled = [...brands, ...brands];
      document.getElementById('tickerTrack').innerHTML =
        doubled.map(b => `<span>${b.brand_name}</span><span class="sep">·</span>`).join('');
    }
  } catch { /* keep default */ }
}

/* ══════════════════════════════════════════════════════════════
   NEWSLETTER
   ══════════════════════════════════════════════════════════════ */
document.getElementById('newsletterForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const emailEl = document.getElementById('newsletterEmail');
  const email   = emailEl.value.trim();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showToast('Please enter a valid email address.');
    emailEl.focus();
    return;
  }
  try {
    await fetch(`${API_BASE}/newsletter/subscribe/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
      signal: AbortSignal.timeout(3000)
    });
  } catch { /* silent fail — show success either way */ }
  showToast('You\'re subscribed — welcome to The Last Note ✨');
  emailEl.value = '';
});

/* ══════════════════════════════════════════════════════════════
   CART BUTTON
   ══════════════════════════════════════════════════════════════ */
/* ══════════════════════════════════════════════════════════════
   PAGE LOADER
   ══════════════════════════════════════════════════════════════ */
window.addEventListener('load', () => {
  setTimeout(() => {
    document.getElementById('loader').classList.add('gone');
  }, 1100);
});

/* ══════════════════════════════════════════════════════════════
   TOAST
   ══════════════════════════════════════════════════════════════ */
let toastTimer;
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}

/* ══════════════════════════════════════════════════════════════
   UTILITIES
   ══════════════════════════════════════════════════════════════ */
const delay = ms => new Promise(r => setTimeout(r, ms));

/* ══════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════ */
loadProducts();
loadBrands();
renderReviews();
window.addEventListener('resize', renderReviews, { passive: true });
