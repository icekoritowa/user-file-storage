const yearElement = document.getElementById("current-year");
if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

const themeButton = document.getElementById("theme-toggle");
if (themeButton) {
    themeButton.hidden = false;
    themeButton.addEventListener("click", () => {
        const dark = document.body.classList.toggle("dark-theme");
        themeButton.setAttribute("aria-pressed", String(dark));
        themeButton.textContent = dark ? "Светлая тема" : "Тёмная тема";
    });
}
