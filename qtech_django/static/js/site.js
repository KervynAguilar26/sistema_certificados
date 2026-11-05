/* QTech public website — small progressive-enhancement helpers. */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    // Mobile navigation.
    var menuToggle = document.querySelector("[data-menu-toggle]");
    var siteNav = document.querySelector("[data-site-nav]");
    if (menuToggle && siteNav) {
      menuToggle.addEventListener("click", function () {
        var open = siteNav.classList.toggle("is-open");
        menuToggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      siteNav.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
          siteNav.classList.remove("is-open");
          menuToggle.setAttribute("aria-expanded", "false");
        });
      });
    }

    // Language dropdown.
    var langToggle = document.querySelector("[data-language-toggle]");
    var langDropdown = document.querySelector("[data-language-dropdown]");
    if (langToggle && langDropdown) {
      langToggle.addEventListener("click", function (event) {
        event.stopPropagation();
        var open = langDropdown.classList.toggle("is-open");
        langToggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      document.addEventListener("click", function () {
        langDropdown.classList.remove("is-open");
        langToggle.setAttribute("aria-expanded", "false");
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          langDropdown.classList.remove("is-open");
          langToggle.setAttribute("aria-expanded", "false");
        }
      });
    }

    // Hero slider.
    var slider = document.querySelector("[data-hero-slider]");
    if (slider) {
      var slides = Array.prototype.slice.call(slider.querySelectorAll("[data-hero-slide]"));
      var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-hero-dot]"));
      var current = 0;
      var timer = null;

      function show(index) {
        if (!slides.length) return;
        current = (index + slides.length) % slides.length;
        slides.forEach(function (slide, i) {
          slide.classList.toggle("is-active", i === current);
        });
        dots.forEach(function (dot, i) {
          dot.classList.toggle("is-active", i === current);
        });
      }

      function next() { show(current + 1); }
      function prev() { show(current - 1); }

      var nextButton = slider.querySelector("[data-hero-next]");
      var prevButton = slider.querySelector("[data-hero-prev]");
      if (nextButton) nextButton.addEventListener("click", function () { next(); restart(); });
      if (prevButton) prevButton.addEventListener("click", function () { prev(); restart(); });
      dots.forEach(function (dot, i) {
        dot.addEventListener("click", function () { show(i); restart(); });
      });

      function start() {
        if (slides.length > 1 && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          timer = window.setInterval(next, 6500);
        }
      }
      function stop() {
        if (timer) { window.clearInterval(timer); timer = null; }
      }
      function restart() { stop(); start(); }

      slider.addEventListener("mouseenter", stop);
      slider.addEventListener("mouseleave", start);
      start();
    }

    // Gallery lightbox.
    var lightbox = document.querySelector("[data-lightbox-modal]");
    var lightboxImage = document.querySelector("[data-lightbox-image]");
    var lightboxClose = document.querySelector("[data-lightbox-close]");
    if (lightbox && lightboxImage) {
      document.querySelectorAll("[data-lightbox]").forEach(function (button) {
        button.addEventListener("click", function () {
          lightboxImage.src = button.getAttribute("data-lightbox");
          lightboxImage.alt = button.getAttribute("data-lightbox-alt") || "";
          lightbox.hidden = false;
          document.body.style.overflow = "hidden";
          if (lightboxClose) lightboxClose.focus();
        });
      });
      function closeLightbox() {
        lightbox.hidden = true;
        lightboxImage.src = "";
        document.body.style.overflow = "";
      }
      if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
      lightbox.addEventListener("click", function (event) {
        if (event.target === lightbox) closeLightbox();
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !lightbox.hidden) closeLightbox();
      });
    }

    // Back-to-top button.
    var backToTop = document.querySelector("[data-back-to-top]");
    if (backToTop) {
      function toggleBackToTop() {
        backToTop.hidden = window.scrollY < 600;
      }
      window.addEventListener("scroll", toggleBackToTop, { passive: true });
      toggleBackToTop();
      backToTop.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }
  });
})();
