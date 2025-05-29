// static/js/scripts.js
function showNotification(message) {
    const notification = document.createElement("div");
    notification.classList.add("notification");
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Example usage:
showNotification("تم تحديث الطلب بنجاح!");