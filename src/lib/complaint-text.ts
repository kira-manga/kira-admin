const directionalControls = /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u206f]/g;

/** Display/copy representation only; never feed it back into stored prose or a retained request. */
export function visibleComplaintText(value: string) {
  return value.replace(directionalControls, (mark) => `[U+${mark.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}]`);
}

export function copyComplaintSelection(event: { currentTarget: HTMLTextAreaElement | HTMLInputElement; clipboardData: DataTransfer; preventDefault: () => void }) {
  const input = event.currentTarget;
  if (input.selectionStart === null || input.selectionEnd === null) return;
  const selected = input.value.slice(input.selectionStart, input.selectionEnd);
  const visible = visibleComplaintText(selected);
  if (visible === selected) return;
  event.preventDefault();
  event.clipboardData.setData('text/plain', visible);
}
