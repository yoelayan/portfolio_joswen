import Lenis from "lenis";

const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// Desplazamiento suave (se omite si la persona prefiere menos movimiento).
if (!reduce) {
  const lenis = new Lenis({ lerp: 0.1, smoothWheel: true, anchors: true });
  const raf = (time) => {
    lenis.raf(time);
    requestAnimationFrame(raf);
  };
  requestAnimationFrame(raf);
}

// El color de la barra de navegación sigue al tema de la sección que tiene debajo.
const nav = document.querySelector(".nav");
const themed = [...document.querySelectorAll("[data-theme]")].filter((el) => el !== nav);

function updateNav() {
  if (!nav || !themed.length) return;
  const y = 36;
  let theme = nav.dataset.theme || "dark";
  for (const el of themed) {
    const rect = el.getBoundingClientRect();
    if (rect.top <= y && rect.bottom > y) {
      theme = el.dataset.theme;
      break;
    }
  }
  nav.dataset.theme = theme;
}

addEventListener("scroll", updateNav, { passive: true });
addEventListener("resize", updateNav);
updateNav();
