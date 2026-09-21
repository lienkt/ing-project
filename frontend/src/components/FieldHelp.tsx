import { QuickGuide } from "./QuickGuide";

export function FieldHelp({ label, help }: { label: string; help: string }) {
  return (
    <QuickGuide label={`Explain ${label}`} title={label}>
      <p className="field-help-description">{help}</p>
    </QuickGuide>
  );
}

export function FieldLabel({
  id,
  label,
  help,
}: {
  id: string;
  label: string;
  help: string;
}) {
  return (
    <div className="field-label-heading">
      <label htmlFor={id}>{label}</label>
      <FieldHelp label={label} help={help} />
    </div>
  );
}
