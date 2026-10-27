'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

let scrollLocks = 0;
let savedOverflow;
let savedOverflowPriority;

// A second modal must not unlock the page while the first is still open.
function lockBodyScroll() {
  const style = document.body.style;
  if (scrollLocks === 0) {
    savedOverflow = style.getPropertyValue('overflow');
    savedOverflowPriority = style.getPropertyPriority('overflow');
    style.setProperty('overflow', 'hidden');
  }
  scrollLocks += 1;
  return () => {
    scrollLocks -= 1;
    if (scrollLocks === 0) {
      if (savedOverflow) style.setProperty('overflow', savedOverflow, savedOverflowPriority);
      else style.removeProperty('overflow');
    }
  };
}

export function useModalDialog(isOpen, onClose) {
  const dialogRef = useRef(null);
  const titleRef = useRef(null);
  const closeRef = useRef(onClose);
  const pathname = usePathname();
  const openedPath = useRef(pathname);

  useEffect(() => { closeRef.current = onClose; }, [onClose]);

  useEffect(() => {
    if (!isOpen) {
      openedPath.current = pathname;
      return;
    }
    if (openedPath.current !== pathname) {
      closeRef.current();
      return;
    }

    const dialog = dialogRef.current;
    const trigger = document.activeElement;
    // Native modality supplies the top layer, inert background and focus containment.
    dialog.showModal();
    const unlockScroll = lockBodyScroll();
    titleRef.current?.focus({ preventScroll: true });

    const cancel = (event) => {
      event.preventDefault();
      closeRef.current();
    };
    const close = () => {
      // Ignore a queued close event from a Strict Mode cleanup after reopening.
      if (!dialog.open) closeRef.current();
    };
    const containTab = (event) => {
      if (event.key !== 'Tab' || event.altKey || event.ctrlKey || event.metaKey) return;
      const controls = [...dialog.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
        .filter((node) => node.tabIndex >= 0 && !node.matches(':disabled') &&
          !node.closest('[inert]') && node.getClientRects().length > 0 &&
          getComputedStyle(node).visibility !== 'hidden');
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (!first) {
        event.preventDefault();
        titleRef.current?.focus({ preventScroll: true });
      } else if (event.shiftKey && (document.activeElement === first || !controls.includes(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    dialog.addEventListener('cancel', cancel);
    dialog.addEventListener('close', close);
    dialog.addEventListener('keydown', containTab);

    return () => {
      dialog.removeEventListener('cancel', cancel);
      dialog.removeEventListener('close', close);
      dialog.removeEventListener('keydown', containTab);
      if (dialog.open) dialog.close();
      unlockScroll();
      if (trigger?.isConnected && !trigger.closest('[inert]') && trigger.getClientRects().length > 0) {
        trigger.focus({ preventScroll: true });
      }
    };
  }, [isOpen, pathname]);

  return { dialogRef, titleRef };
}
