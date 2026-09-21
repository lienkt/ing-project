import { CircleDashed, PencilLine, CircleCheck, RotateCcw } from "lucide-react";
import { QuickGuide } from "./QuickGuide";

export function LabelingStatusHelp() {
  return (
    <QuickGuide label="Explain labeling statuses" title="What does each status mean?">
      <dl className="status-help-list">
        <div className="status-help-item status-help-idle">
          <dt>
            <CircleDashed size={18} aria-hidden="true" />
            Not Started
          </dt>
          <dd>No labels saved yet.</dd>
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
    </QuickGuide>
  );
}
