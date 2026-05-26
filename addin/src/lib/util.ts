// Lokales ISO ohne Zeitzonenversatz, damit Uhrzeiten korrekt angezeigt werden.
export function toLocalIso(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:00`
  );
}

export function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max)} […]` : text;
}
