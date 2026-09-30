/** @type {import('next').NextConfig} */
// FRAME_ANCESTORS: sayfayı iframe ile gömebilecek siteler (boşlukla ayrılmış),
// örn. FRAME_ANCESTORS="https://yummylightstore.com https://www.yummylightstore.com"
// Boşsa her site gömebilir.
const frameAncestors = (process.env.FRAME_ANCESTORS || "").trim();

module.exports = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
  },
  async headers() {
    if (!frameAncestors) return [];
    return [{
      source: "/:path*",
      headers: [{ key: "Content-Security-Policy", value: `frame-ancestors 'self' ${frameAncestors}` }],
    }];
  },
};
