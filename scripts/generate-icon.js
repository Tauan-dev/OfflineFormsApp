/**
 * Gera assets/icon-generated.png e assets/adaptive-icon-generated.png:
 *  - Canvas 1024×1024, fundo branco
 *  - Logo centralizada ocupando ~55% da área (margem de ~22% em cada lado)
 *
 * Uso: node scripts/generate-icon.js
 */

const { Jimp } = require("jimp");
const path = require("path");

const SRC          = path.resolve(__dirname, "../assets/coletaverdelogo.png");
const OUT_ICON     = path.resolve(__dirname, "../assets/icon-generated.png");
const OUT_ADAPTIVE = path.resolve(__dirname, "../assets/adaptive-icon-generated.png");

const CANVAS = 1024;
const LOGO_SIZE_ICON     = Math.round(CANVAS * 0.55); // 563px — icon normal
const LOGO_SIZE_ADAPTIVE = Math.round(CANVAS * 0.48); // 491px — dentro da safe zone do Android

async function generate() {
  const logo = await Jimp.read(SRC);

  // ── icon.png ──────────────────────────────────────────────────────────────
  const iconCanvas = new Jimp({ width: CANVAS, height: CANVAS, color: 0xffffffff });
  const iconLogo = logo.clone().resize({ w: LOGO_SIZE_ICON });
  const iconX = Math.round((CANVAS - iconLogo.width) / 2);
  const iconY = Math.round((CANVAS - iconLogo.height) / 2);
  iconCanvas.composite(iconLogo, iconX, iconY);
  await iconCanvas.write(OUT_ICON);
  console.log("✅ icon-generated.png salvo em assets/");

  // ── adaptive-icon.png ─────────────────────────────────────────────────────
  const adaptiveCanvas = new Jimp({ width: CANVAS, height: CANVAS, color: 0xffffffff });
  const adaptiveLogo = logo.clone().resize({ w: LOGO_SIZE_ADAPTIVE });
  const adaptiveX = Math.round((CANVAS - adaptiveLogo.width) / 2);
  const adaptiveY = Math.round((CANVAS - adaptiveLogo.height) / 2);
  adaptiveCanvas.composite(adaptiveLogo, adaptiveX, adaptiveY);
  await adaptiveCanvas.write(OUT_ADAPTIVE);
  console.log("✅ adaptive-icon-generated.png salvo em assets/");
}

generate().catch((err) => {
  console.error("Erro ao gerar ícone:", err);
  process.exit(1);
});

