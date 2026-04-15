# ── Stage 1: deps ────────────────────────────────────────────────────────────
# Install node_modules separately from source for better layer caching.
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files — use package-lock.json if present (npm ci), else npm install
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --ignore-scripts; else npm install --ignore-scripts; fi

# ── Stage 2: builder ─────────────────────────────────────────────────────────
# Build the Next.js standalone output.
FROM node:20-alpine AS builder

WORKDIR /app

# NEXT_PUBLIC_* env vars must be available at build time
# They are passed as Docker build arguments and baked into the static bundle.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_SHOW_DEV_PANEL=false

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_SHOW_DEV_PANEL=$NEXT_PUBLIC_SHOW_DEV_PANEL

# Next.js telemetry — opt out for CI/CD
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build Next.js app with standalone output
RUN npm run build

# ── Stage 3: runner ───────────────────────────────────────────────────────────
# Minimal production image — only the standalone bundle and public assets.
FROM node:20-alpine AS runner

WORKDIR /app

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy only the standalone output from the builder
# Use shell form + mkdir to handle an empty or absent public/ directory gracefully
RUN mkdir -p ./public
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME=0.0.0.0

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
