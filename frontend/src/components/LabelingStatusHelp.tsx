import { useEffect, useId, useRef, useState } from "react";
import {
  CircleDashed,
  Sparkles,
  PencilLine,
  CircleCheck,
  RotateCcw,
} from "lucide-react";
import { createPortal } from "react-dom";

export function LabelingStatusHelp() {
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
        aria-label="Explain labeling statuses"
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
              <strong>What does each status mean?</strong>
            </header>
            <dl className="status-help-list">
              <div className="status-help-item status-help-idle">
                <dt>
                  <CircleDashed size={18} aria-hidden="true" />
                  Not Started
                </dt>
                <dd>No labels saved yet.</dd>
              </div>
              <div className="status-help-item status-help-auto">
                <dt>
                  <Sparkles size={18} aria-hidden="true" />
                  Auto Suggested
                </dt>
                <dd>Suggestions are ready for your review. Not saved as labels yet.</dd>
              </div>
              <div className="status-help-item status-help-draft">
                <dt>
                  <PencilLine size={18} aria-hidden="true" />
                  In Progress
                </dt>
                <dd>Draft saved. Finish reviewing, then click Complete Labeling.</dd>
              </div>
              <div className="status-help-item status-help-done">
                <dt>
                  <CircleCheck size={18} aria-hidden="true" />
                  Completed
                </dt>
                <dd>Review confirmed. Some fields may still be unset.</dd>
              </div>
            </dl>
            <p className="status-help-note">
              <RotateCcw size={16} aria-hidden="true" />
              <span>
                Editing and saving completed labels returns them to{" "}
                <strong>In Progress</strong>.
              </span>
            </p>
          </div>,
          document.body,
        )}
    </>
  );
}
