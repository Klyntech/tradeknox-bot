import { NextResponse } from "next/server";

const TWELVEDATA_API_KEY = process.env.TWELVEDATA_API_KEY || "";
const PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "GBPJPY"];
let cache: { data: Record<string, { p: number; c: number }> | null; ts: number } = { data: null, ts: 0 };

export const revalidate = 0;

export async function GET() {
  const now = Date.now();
  if (cache.data && now - cache.ts < 30000) {
    return NextResponse.json(cache.data);
  }

  if (!TWELVEDATA_API_KEY) {
    return NextResponse.json({ error: "no api key" }, { status: 503 });
  }

  try {
    const symbols = PAIRS.join(",");
    const r = await fetch(
      `https://api.twelvedata.com/quote?symbol=${symbols}&apikey=${TWELVEDATA_API_KEY}`,
      { next: { revalidate: 30 } }
    );
    const raw = await r.json();
    const out: Record<string, { p: number; c: number }> = {};

    for (const [sym, val] of Object.entries(raw)) {
      if (typeof val === "object" && val !== null && "percent_change" in (val as Record<string, unknown>)) {
        const v = val as Record<string, unknown>;
        out[sym] = {
          p: parseFloat(String(v.close || 0)),
          c: parseFloat(String(v.percent_change || 0)),
        };
      }
    }

    if (Object.keys(out).length > 0) {
      cache = { data: out, ts: now };
    }

    return NextResponse.json(out);
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}