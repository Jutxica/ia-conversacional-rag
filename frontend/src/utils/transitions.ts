import { animate as anime, stagger } from 'animejs';

export const fadeIn = (targets: string | HTMLElement | HTMLElement[]) => {
  return anime({
    targets,
    opacity: [0, 1],
    translateY: [10, 0],
    duration: 800,
    easing: 'easeOutQuart'
  });
};

export const slideInSidebar = (targets: string | HTMLElement) => {
  return anime({
    targets,
    translateX: ['-100%', '0%'],
    duration: 600,
    easing: 'easeOutExpo'
  });
};

export const stagerReveal = (targets: string | HTMLElement[]) => {
  return anime({
    targets,
    opacity: [0, 1],
    translateY: [20, 0],
    delay: stagger(100),
    duration: 800,
    easing: 'easeOutBack'
  });
};

export const magneticEffect = (element: HTMLElement) => {
  if (!element) return;

  element.addEventListener('mousemove', (e: MouseEvent) => {
    const { left, top, width, height } = element.getBoundingClientRect();
    const x = e.clientX - (left + width / 2);
    const y = e.clientY - (top + height / 2);

    anime({
      targets: element,
      translateX: x * 0.3,
      translateY: y * 0.3,
      duration: 300,
      easing: 'easeOutQuad'
    });
  });

  element.addEventListener('mouseleave', () => {
    anime({
      targets: element,
      translateX: 0,
      translateY: 0,
      duration: 500,
      easing: 'easeOutElastic(1, .5)'
    });
  });
};
