import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import { z } from "zod";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  simulation: router({
    getLatestData: publicProcedure.query(() => ({
      timestamp: Date.now(),
      targets: [],
      system_health: {
        battery: 100,
        cpu: 15,
        snr: 95,
        temperature: 42,
        interceptorsReady: 12,
        muhimmat: 50,
      },
      current_stage: 1,
      auto_fire_enabled: true,
      radar_emission: true,
      weather: "CLEAR",
    })),

    sendCommand: publicProcedure
      .input(z.object({
        action: z.enum([
          "set_stage_1", "set_stage_2", "set_stage_3",
          "manual_fire", "force_swarm", "trigger_emp",
          "toggle_auto_fire", "toggle_radar_emission", "toggle_weather",
          "trigger_estop", "release_estop"
        ]),
        target_id: z.string().optional(),
      }))
      .mutation(({ input }) => {
        try {
          fetch("http://localhost:8000/api/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(input),
          }).catch(err => console.error("Simulasyon komut hatasi:", err));
        } catch (error) {
          console.error("Komut gonderme hatasi:", error);
        }
        return { success: true };
      }),
  }),
});

export type AppRouter = typeof appRouter;
