import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Caractr — O preço deste carro usado é justo?";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "1200px",
          height: "630px",
          background: "#0D0C0A",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "flex-end",
          padding: "72px 80px",
          fontFamily: "sans-serif",
          position: "relative",
        }}
      >
        {/* Decorative accent bar */}
        <div style={{
          position: "absolute",
          top: "72px",
          left: "80px",
          width: "48px",
          height: "3px",
          background: "#C8A882",
          borderRadius: "2px",
        }} />

        {/* Tagline */}
        <p style={{
          fontSize: "18px",
          color: "#C8A882",
          letterSpacing: "0.15em",
          textTransform: "uppercase",
          marginBottom: "20px",
          fontWeight: 400,
        }}>
          Carros usados em Portugal
        </p>

        {/* Main headline */}
        <h1 style={{
          fontSize: "72px",
          fontWeight: 800,
          color: "#F2EFE9",
          letterSpacing: "-0.02em",
          lineHeight: 0.95,
          marginBottom: "32px",
        }}>
          CARACTR
        </h1>

        {/* Description */}
        <p style={{
          fontSize: "22px",
          color: "#9A9590",
          fontWeight: 300,
          maxWidth: "700px",
          lineHeight: 1.5,
        }}>
          Cola o link do anúncio: preço justo, problemas conhecidos do motor
          e o que verificar antes de comprar.
        </p>

        {/* Bottom URL */}
        <p style={{
          position: "absolute",
          bottom: "72px",
          right: "80px",
          fontSize: "16px",
          color: "#9A9590",
          letterSpacing: "0.08em",
        }}>
          caractr.pt
        </p>
      </div>
    ),
    size,
  );
}
