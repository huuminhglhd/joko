/* ==========================================================================
   JOKO WEB APPLICATION ENGINE (joko.mom)
   Interactive Cart, Zalo Direct Checkout, Franchise Lead Flow & Responsive Controls
   Hotline / Zalo: 0962.869.295
   ========================================================================== */

// Global State
let cartState = [];

// DOM Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  initScrollHeader();
  updateCartUI();
});

/* --------------------------------------------------------------------------
   HEADER & DRAWER CONTROLS
   -------------------------------------------------------------------------- */
function initScrollHeader() {
  const header = document.getElementById('header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });
}

function toggleMobileDrawer() {
  const drawer = document.getElementById('mobile-drawer');
  if (drawer) {
    drawer.classList.toggle('open');
  }
}

/* --------------------------------------------------------------------------
   MENU CARDS & SIZE PICKER
   -------------------------------------------------------------------------- */
function selectCardSize(buttonEl) {
  const sizeContainer = buttonEl.closest('.size-options');
  if (!sizeContainer) return;

  // Remove active from sibling size buttons
  sizeContainer.querySelectorAll('.size-btn').forEach(btn => btn.classList.remove('active'));
  buttonEl.classList.add('active');

  // Update card price display
  const price = buttonEl.getAttribute('data-price');
  const dishCard = buttonEl.closest('.dish-card');
  if (dishCard && price) {
    const priceDisplay = dishCard.querySelector('.dish-price-display');
    if (priceDisplay) {
      priceDisplay.textContent = formatCurrency(parseInt(price, 10));
    }
  }
}

function filterMenu(category) {
  // Update active tab button
  const tabs = document.querySelectorAll('.menu-tabs .tab-btn');
  tabs.forEach(tab => tab.classList.remove('active'));
  
  const activeTab = Array.from(tabs).find(t => t.getAttribute('onclick').includes(`'${category}'`));
  if (activeTab) activeTab.classList.add('active');

  // Filter dish cards
  const cards = document.querySelectorAll('#menu-grid-container .dish-card');
  cards.forEach(card => {
    const cardCat = card.getAttribute('data-category');
    if (category === 'all' || cardCat === category) {
      card.style.display = 'flex';
      card.style.animation = 'fadeIn 0.4s ease forwards';
    } else {
      card.style.display = 'none';
    }
  });
}

/* --------------------------------------------------------------------------
   INTERACTIVE CART ENGINE
   -------------------------------------------------------------------------- */
function addDishToCart(buttonEl, dishName) {
  const dishCard = buttonEl.closest('.dish-card');
  if (!dishCard) return;

  const activeSizeBtn = dishCard.querySelector('.size-btn.active');
  const size = activeSizeBtn ? activeSizeBtn.getAttribute('data-size') : 'Chuẩn';
  const price = activeSizeBtn ? parseInt(activeSizeBtn.getAttribute('data-price'), 10) : 0;

  // Check if item already exists in cart with same size
  const existingIndex = cartState.findIndex(item => item.name === dishName && item.size === size);

  if (existingIndex > -1) {
    cartState[existingIndex].qty += 1;
  } else {
    cartState.push({
      name: dishName,
      size: size,
      price: price,
      qty: 1
    });
  }

  updateCartUI();
  showToast(`✅ Đã thêm ${dishName} (${size}) vào giỏ món!`);

  // Optional: Auto open cart modal on first item
  if (cartState.reduce((sum, item) => sum + item.qty, 0) === 1) {
    toggleCartModal();
  }
}

function changeItemQty(index, delta) {
  if (cartState[index]) {
    cartState[index].qty += delta;
    if (cartState[index].qty <= 0) {
      cartState.splice(index, 1);
    }
  }
  updateCartUI();
}

function updateCartUI() {
  const cartCountBadges = [document.getElementById('cart-count'), document.getElementById('fab-cart-count')];
  const itemsContainer = document.getElementById('cart-items-container');
  const emptyMsg = document.getElementById('cart-empty-msg');
  const summaryBox = document.getElementById('cart-summary-box');
  const modalFooter = document.getElementById('cart-modal-footer');
  const totalPriceEl = document.getElementById('cart-total-price');

  const totalQty = cartState.reduce((sum, item) => sum + item.qty, 0);
  const totalPrice = cartState.reduce((sum, item) => sum + (item.price * item.qty), 0);

  // Update badge numbers
  cartCountBadges.forEach(badge => {
    if (badge) badge.textContent = totalQty;
  });

  // Render items list
  if (itemsContainer) {
    itemsContainer.innerHTML = '';
    
    if (cartState.length === 0) {
      if (emptyMsg) emptyMsg.style.display = 'block';
      if (summaryBox) summaryBox.style.display = 'none';
      if (modalFooter) modalFooter.style.display = 'none';
    } else {
      if (emptyMsg) emptyMsg.style.display = 'none';
      if (summaryBox) summaryBox.style.display = 'block';
      if (modalFooter) modalFooter.style.display = 'block';

      cartState.forEach((item, index) => {
        const row = document.createElement('div');
        row.className = 'cart-item-row';
        row.innerHTML = `
          <div class="cart-item-info">
            <strong>${item.name}</strong>
            <span>${item.size} — ${formatCurrency(item.price)}</span>
          </div>
          <div class="cart-item-controls">
            <button class="qty-btn" onclick="changeItemQty(${index}, -1)">-</button>
            <span class="qty-num">${item.qty}</span>
            <button class="qty-btn" onclick="changeItemQty(${index}, 1)">+</button>
          </div>
        `;
        itemsContainer.appendChild(row);
      });
    }
  }

  if (totalPriceEl) {
    totalPriceEl.textContent = formatCurrency(totalPrice);
  }
}

function toggleCartModal() {
  const modal = document.getElementById('cart-modal');
  if (modal) {
    modal.classList.toggle('open');
  }
}

/* --------------------------------------------------------------------------
   ZALO DIRECT CHECKOUT INTEGRATION
   -------------------------------------------------------------------------- */
function submitCartToZalo() {
  if (cartState.length === 0) {
    alert('Giỏ hàng của bạn chưa có món nào!');
    return;
  }

  const nameInput = document.getElementById('c-name');
  const phoneInput = document.getElementById('c-phone');
  const addressInput = document.getElementById('c-address');
  const noteInput = document.getElementById('c-note');

  const name = nameInput ? nameInput.value.trim() : '';
  const phone = phoneInput ? phoneInput.value.trim() : '';
  const address = addressInput ? addressInput.value.trim() : '';
  const note = noteInput ? noteInput.value.trim() : '';

  if (!name || !phone || !address) {
    alert('Vui lòng điền đầy đủ Họ tên, Số điện thoại và Địa chỉ giao hàng!');
    return;
  }

  // Format order items for Zalo text message
  let itemsText = cartState.map((item, i) => 
    `${i + 1}. ${item.name} (${item.size}) x${item.qty} = ${formatCurrency(item.price * item.qty)}`
  ).join('\n');

  const totalPrice = cartState.reduce((sum, item) => sum + (item.price * item.qty), 0);

  const zaloMessage = `🔥 ĐƠN ĐẶT MÓN MANG VỀ JOKO (joko.mom)
----------------------------------
👤 Khách hàng: ${name}
📞 Số điện thoại: ${phone}
📍 Địa chỉ giao: ${address}
📝 Ghi chú: ${note || 'Không có'}
----------------------------------
🛒 DANH SÁCH MÓN ĐẶT:
${itemsText}
----------------------------------
💰 TỔNG CỘNG: ${formatCurrency(totalPrice)}

(Xin vui lòng xác nhận đơn hàng và thời gian giao ship cho em!)`;

  // Encode message for Zalo URL payload
  const encodedText = encodeURIComponent(zaloMessage);
  const zaloUrl = `https://zalo.me/0962869295?text=${encodedText}`;

  // Direct redirect to Zalo
  window.open(zaloUrl, '_blank');
}

/* --------------------------------------------------------------------------
   B2B FRANCHISE LEAD FORM ENGINE
   -------------------------------------------------------------------------- */
function handleFranchiseSubmit(event) {
  event.preventDefault();

  const name = document.getElementById('f-name')?.value.trim() || '';
  const phone = document.getElementById('f-phone')?.value.trim() || '';
  const region = document.getElementById('f-region')?.value.trim() || '';
  const capital = document.getElementById('f-capital')?.value || '';
  const note = document.getElementById('f-note')?.value.trim() || '';

  if (!name || !phone || !region) {
    alert('Vui lòng điền các thông tin bắt buộc (*)!');
    return;
  }

  const franchiseMessage = `🤝 ĐĂNG KÝ TƯ VẤN NHƯỢNG QUYỀN JOKO (B2B)
----------------------------------
👤 Nhà đầu tư: ${name}
📞 Số điện thoại / Zalo: ${phone}
📍 Khu vực muốn mở: ${region}
💰 Vốn dự kiến: ${capital}
📝 Ghi chú / Yêu cầu: ${note || 'Cần gửi hồ sơ thông tin chi tiết qua Zalo'}
----------------------------------
(Yêu cầu Bộ phận Nhượng quyền JOKO liên hệ tư vấn trực tiếp trong 24h)`;

  const encodedText = encodeURIComponent(franchiseMessage);
  const zaloUrl = `https://zalo.me/0962869295?text=${encodedText}`;

  alert(`Cảm ơn ${name}! Thông tin của bạn đã được tiếp nhận. Hệ thống sẽ mở Zalo để kết nối trực tiếp với Giám sát Nhượng quyền JOKO (0962.869.295).`);
  
  window.open(zaloUrl, '_blank');
}

/* --------------------------------------------------------------------------
   UTILITY HELPERS
   -------------------------------------------------------------------------- */
function formatCurrency(amount) {
  return amount.toLocaleString('vi-VN') + 'đ';
}

function showToast(msg) {
  let toast = document.getElementById('joko-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'joko-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(26, 17, 14, 0.95);
      color: #F7C04A;
      padding: 0.8rem 1.6rem;
      border-radius: 999px;
      font-size: 0.9rem;
      font-weight: 700;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      z-index: 9999;
      transition: opacity 0.3s ease;
      border: 1px solid rgba(228, 168, 83, 0.4);
      text-align: center;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';

  setTimeout(() => {
    toast.style.opacity = '0';
  }, 2800);
}
