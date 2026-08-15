(() => {
  "use strict";
  const config = window.HINDSFOOT_PUBLIC_CONFIG || {};
  const localPreview = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  const localLogin = localPreview ? `${location.protocol}//${location.hostname}:5000/` : "";
  const loginUrl = config.loginUrl || localLogin || "#login-not-configured";
  document.querySelectorAll(".js-login-link").forEach((link) => {
    link.href = loginUrl;
    if (loginUrl === "#login-not-configured") link.setAttribute("aria-label", "Log In — destination must be configured");
  });

  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-site-nav]");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.dataset.open !== "true";
      nav.dataset.open = String(open);
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        nav.dataset.open = "false";
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  const form = document.querySelector("[data-demo-form]");
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const status = document.querySelector("[data-form-status]");
      if (status) status.textContent = "Preview only — no information was collected or transmitted. A submission destination must be configured before use.";
    });
  }

  const contact = document.querySelector("[data-contact-email]");
  if (contact && config.contactEmail) {
    contact.href = `mailto:${config.contactEmail}?subject=${encodeURIComponent("Hindsfoot demonstration request")}`;
    contact.textContent = config.contactEmail;
    contact.hidden = false;
  }

  document.querySelectorAll("[data-privacy-link]").forEach((link) => {
    link.href = config.privacyPolicyUrl || "privacy.html";
  });
})();
