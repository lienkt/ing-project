import { ReactNode, useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

export function AddSourceDialog({
  children,
  saving,
  onClose,
}: {
  children: ReactNode;
  saving: boolean;
  onClose: () => void;
}) {
  const headingId = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    dialog.current?.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflow;
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus();
    };
  }, []);

  return createPortal(
    <dialog
      ref={dialog}
      className="capture-dialog add-source-dialog"
      aria-labelledby={headingId}
      onCancel={(event) => {
        event.preventDefault();
        if (!saving) onClose();
      }}
    >
      <section className="capture-viewer card">
        <header className="capture-heading">
          <h2 id={headingId}>Add product source</h2>
          <button
            type="button"
            className="secondary"
            aria-label="Close add product source"
            disabled={saving}
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>
        <div className="capture-body">{children}</div>
      </section>
    </dialog>,
    document.body,
  );
}
