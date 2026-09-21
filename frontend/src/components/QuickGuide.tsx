import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

export function QuickGuide({
  label,
  title,
  children,
}: {
  label: string;
  title: string;
  children: ReactNode;
}) {
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pinned = useRef(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  function cancelClose() {
    if (timer.current) clearTimeout(timer.current);
  }
  function close() {
    cancelClose();
    pinned.current = false;
    setPosition(null);
  }
  function open() {
    cancelClose();
    const rect = button.current?.getBoundingClientRect();
    if (rect)
      setPosition({
        top: rect.bottom + 8,
        left: Math.max(12, Math.min(rect.right - 320, window.innerWidth - 332)),
      });
  }
  function leave() {
    cancelClose();
    if (!pinned.current) timer.current = setTimeout(() => setPosition(null), 150);
  }
  useEffect(() => {
    function outside(event: PointerEvent) {
      if (
        !button.current?.contains(event.target as Node) &&
        !panel.current?.contains(event.target as Node)
      )
        close();
    }
    function key(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }
    window.addEventListener("pointerdown", outside);
    window.addEventListener("keydown", key);
    window.addEventListener("resize", close);
    window.addEventListener("scroll", close);
    return () => {
      cancelClose();
      window.removeEventListener("pointerdown", outside);
      window.removeEventListener("keydown", key);
      window.removeEventListener("resize", close);
      window.removeEventListener("scroll", close);
    };
  }, []);
  return (
    <>
      <button
        ref={button}
        type="button"
        className="labeling-help-button"
        aria-label={label}
        aria-expanded={position !== null}
        aria-describedby={position ? id : undefined}
        onMouseEnter={open}
        onMouseLeave={leave}
        onFocus={open}
        onBlur={close}
        onClick={() => {
          if (pinned.current) close();
          else {
            pinned.current = true;
            open();
          }
        }}
      >
        ?
      </button>
      {position &&
        createPortal(
          <div
            ref={panel}
            id={id}
            role="tooltip"
            className="labeling-help-panel"
            style={{
              ...position,
              maxHeight: Math.max(120, window.innerHeight - position.top - 12),
            }}
            onMouseEnter={cancelClose}
            onMouseLeave={leave}
          >
            <header className="status-help-heading">
              <span>QUICK GUIDE</span>
              <strong>{title}</strong>
            </header>
            {children}
          </div>,
          document.body,
        )}
    </>
  );
}
