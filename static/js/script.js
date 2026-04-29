function showPopup() {
    let popup = document.createElement("div");
    popup.innerText = "✅ Added to Cart";
    popup.className = "popup";

    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 2000);
}

<script>
function liveSearch() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let items = document.getElementsByClassName("product-item");

    for (let i = 0; i < items.length; i++) {
        let name = items[i].getElementsByClassName("product-name")[0].innerText.toLowerCase();

        if (name.includes(input)) {
            items[i].style.display = "block";
        } else {
            items[i].style.display = "none";
        }
    }
}
</script>

