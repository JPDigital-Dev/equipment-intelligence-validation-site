document.addEventListener("DOMContentLoaded", () => {
    const navbar = document.querySelector(".navbar");
    const navLinks = document.querySelectorAll(".nav-links a");
    const revealItems = document.querySelectorAll(".reveal");
    const counterItems = document.querySelectorAll("[data-counter]");
    const faqItems = document.querySelectorAll(".faq-item");
    const form = document.getElementById("earlyAccessForm");

    const setNavbarState = () => {
        if (!navbar) return;
        navbar.classList.toggle("scrolled", window.scrollY > 24);
    };

    setNavbarState();
    window.addEventListener("scroll", setNavbarState);

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (event) => {
            const targetId = anchor.getAttribute("href");
            if (!targetId || targetId === "#") return;

            const target = document.querySelector(targetId);
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    revealItems.forEach((item) => revealObserver.observe(item));

    const animateCounter = (element) => {
        const target = Number(element.dataset.counter || 0);
        const duration = 1200;
        const start = performance.now();

        const tick = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = Math.round(target * eased);
            if (progress < 1) {
                requestAnimationFrame(tick);
            }
        };

        requestAnimationFrame(tick);
    };

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.6 });

    counterItems.forEach((item) => counterObserver.observe(item));

    faqItems.forEach((item) => {
        const question = item.querySelector(".faq-question");
        question?.addEventListener("click", () => {
            item.classList.toggle("open");
        });
    });

    const sections = [...document.querySelectorAll("main section[id]")];
    const updateActiveNav = () => {
        const scrollPosition = window.scrollY + 140;
        let current = "";

        sections.forEach((section) => {
            if (scrollPosition >= section.offsetTop) {
                current = section.id;
            }
        });

        navLinks.forEach((link) => {
            const href = link.getAttribute("href");
            link.classList.toggle("active", href === `#${current}`);
        });
    };

    updateActiveNav();
    window.addEventListener("scroll", updateActiveNav);

    if (form) {
        form.addEventListener("submit", (event) => {
            const requiredFields = form.querySelectorAll("[required]");
            let isValid = true;

            requiredFields.forEach((field) => {
                const value = field.value.trim();
                field.value = value;
                field.style.borderColor = "";

                if (!value) {
                    isValid = false;
                    field.style.borderColor = "rgba(255, 107, 129, 0.75)";
                }

                if (field.type === "email" && value && !value.includes("@")) {
                    isValid = false;
                    field.style.borderColor = "rgba(255, 107, 129, 0.75)";
                }
            });

            if (!isValid) {
                event.preventDefault();
            }
        });
    }
});
