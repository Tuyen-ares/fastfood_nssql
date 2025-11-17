// Main JavaScript file

// Add to cart functionality
function addToCart(menuId, quantity = 1) {
    fetch('/customer/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `menu_id=${menuId}&quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cart count in navbar
            const cartBadge = document.querySelector('.navbar .badge');
            if (cartBadge) {
                cartBadge.textContent = data.cart_count;
            }
            
            // Show success message
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

