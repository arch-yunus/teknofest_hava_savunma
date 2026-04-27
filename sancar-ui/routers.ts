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
          // Katman Seçimi (Türkçe)
          "katman_yildirim", "katman_hanc", "katman_kalkan", "katman_isin", "katman_avci",
          // Çalışma Modu (Türkçe)
          "mod_otomatik", "mod_yari_otomatik", "mod_manuel",
          // İşlem Kontrolleri (Türkçe)
          "manuel_ates", "suru_saldirisi", "lazer_engajmani",
          // Sistem Kontrolleri (Türkçe)
          "radar_yayini_ac", "radar_yayini_kapat",
          "hava_etkinlestir", "hava_devre_disi_birak",
          "acil_durdur", "acil_durdur_kaldir",
          // Eski komutlar (uyumluluk için)
          "set_stage_1", "set_stage_2", "set_stage_3",
          "manual_fire", "force_swarm", "trigger_emp",
          "toggle_auto_fire", "toggle_radar_emission", "toggle_weather",
          "trigger_estop", "release_estop"
        ]),
        target_id: z.string().optional(),
        layer_id: z.number().optional(),
      }))
      .mutation(({ input }) => {
        // Türkçe komutları İngilizce'ye çevir (simulasyon uyumluluğu için)
        const commandMap: Record<string, string> = {
          "katman_yildirim": "set_stage_1",
          "katman_hanc": "set_stage_2",
          "katman_kalkan": "set_stage_3",
          "katman_isin": "toggle_weather",
          "katman_avci": "manual_fire",
          "mod_otomatik": "toggle_auto_fire",
          "mod_yari_otomatik": "toggle_auto_fire",
          "mod_manuel": "toggle_auto_fire",
          "manuel_ates": "manual_fire",
          "suru_saldirisi": "force_swarm",
          "lazer_engajmani": "trigger_emp",
          "radar_yayini_ac": "toggle_radar_emission",
          "radar_yayini_kapat": "toggle_radar_emission",
          "hava_etkinlestir": "toggle_weather",
          "hava_devre_disi_birak": "toggle_weather",
          "acil_durdur": "trigger_estop",
          "acil_durdur_kaldir": "release_estop",
        };

        const mappedAction = commandMap[input.action] || input.action;

        try {
          fetch("http://localhost:8000/api/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              action: mappedAction,
              target_id: input.target_id,
              layer_id: input.layer_id,
              original_command: input.action,
            }),
          }).catch(err => console.error("Simulasyon komut hatasi:", err));
        } catch (error) {
          console.error("Komut gonderme hatasi:", error);
        }
        return { success: true };
      }),
  }),
});

export type AppRouter = typeof appRouter;
