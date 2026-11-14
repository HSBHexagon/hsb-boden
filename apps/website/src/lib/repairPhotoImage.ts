const MAX_EDGE = 1600;
const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

type Drawable = { source: CanvasImageSource; width: number; height: number; release(): void };

/** Dekodiert das Foto: zuerst mit EXIF-Ausrichtung, dann ohne Optionen (ältere Safari-Versionen), zuletzt über <img>. */
async function decode(file: File): Promise<Drawable> {
  for (const options of [{ imageOrientation: "from-image" } as ImageBitmapOptions, undefined]) {
    try {
      const bitmap = await createImageBitmap(file, options);
      return { source: bitmap, width: bitmap.width, height: bitmap.height, release: () => bitmap.close() };
    } catch {
      // Nächsten Weg versuchen.
    }
  }
  const url = URL.createObjectURL(file);
  const img = new Image();
  img.src = url;
  try {
    await img.decode();
  } catch (error) {
    URL.revokeObjectURL(url);
    throw error;
  }
  return { source: img, width: img.naturalWidth, height: img.naturalHeight, release: () => URL.revokeObjectURL(url) };
}

/** Verkleinert auf max. 1600 px und speichert als JPEG neu; dabei gehen EXIF-/GPS-Daten verloren. */
export async function shrink(file: File): Promise<Blob> {
  try {
    const image = await decode(file);
    const scale = Math.min(1, MAX_EDGE / Math.max(image.width, image.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(image.width * scale);
    canvas.height = Math.round(image.height * scale);
    try {
      const context = canvas.getContext("2d");
      if (!context) throw new Error("canvas_unavailable");
      context.drawImage(image.source, 0, 0, canvas.width, canvas.height);
    } finally {
      image.release();
    }
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.82));
    if (blob && blob.size <= MAX_UPLOAD_BYTES) return blob;
  } catch {
    // Keine Originaldatei senden: dort könnten EXIF- und GPS-Metadaten enthalten sein.
  }
  throw new Error("unsupported");
}

