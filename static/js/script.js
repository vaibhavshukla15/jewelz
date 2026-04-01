function showPopup() {
    let popup = document.createElement("div");
    popup.innerText = "✅ Added to Cart";
    popup.className = "popup";

    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 2000);
}