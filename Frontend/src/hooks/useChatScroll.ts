import { useEffect, useRef } from 'react';

export const useChatScroll = <T extends HTMLElement>(dep: unknown) => {
  const containerRef = useRef<T | null>(null);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    node.querySelector<HTMLElement>(':scope > :last-child')?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  }, [dep]);

  return containerRef;
};
