function toggleMenu() {
  const menu = document.getElementById("popupMenu");
  menu.style.display = menu.style.display === "block" ? "none" : "block";
}

document.addEventListener("click", function(event) {
  const menu = document.getElementById("popupMenu");
  const btn = document.getElementById("menuBtn");
  if (!menu.contains(event.target) && !btn.contains(event.target)) {
    menu.style.display = "none";
  }
});

function changeSize() {
  const size = document.getElementById("sizeFilter").value;
  const items = document.querySelectorAll(".media-item img, .media-item video");

  items.forEach(el => {
    if (size === "normal") {
      el.style.maxWidth = "200px";
      el.style.maxHeight = "150px";
    } else if (size === "medium") {
      el.style.maxWidth = "400px";
      el.style.maxHeight = "300px";
    } else if (size === "large") {
      el.style.maxWidth = "800px";
      el.style.maxHeight = "600px";
    } else if (size === "original") {
      el.style.maxWidth = "100%";
      el.style.maxHeight = "100%";
    }
  });
}
