// Saldao Center - Hub de Marketing
// Cole este codigo no step Node.js do Pipedream

export default defineComponent({
  props: {
    google_analytics: {
      type: "app",
      app: "google_analytics",
    },
    google_ads: {
      type: "app",
      app: "google_ads",
    }
  },

  async run({ steps, $ }) {
    const { action, params } = steps.trigger.event.body;

    // Roteador de acoes
    switch(action) {

      // ===== GOOGLE ANALYTICS =====
      case "ga_overview":
        return await this.getAnalyticsOverview(params);

      case "ga_realtime":
        return await this.getAnalyticsRealtime(params);

      case "ga_report":
        return await this.getAnalyticsReport(params);

      // ===== GOOGLE ADS =====
      case "ads_campaigns":
        return await this.getAdsCampaigns(params);

      case "ads_performance":
        return await this.getAdsPerformance(params);

      // ===== INFO =====
      case "help":
      default:
        return this.getHelp();
    }
  },

  // Lista de comandos disponiveis
  getHelp() {
    return {
      success: true,
      message: "Saldao Center Marketing Hub",
      actions: {
        google_analytics: [
          { action: "ga_overview", desc: "Visao geral do site (sessoes, usuarios, pageviews)" },
          { action: "ga_realtime", desc: "Usuarios ativos agora" },
          { action: "ga_report", desc: "Relatorio customizado", params: ["startDate", "endDate", "metrics"] }
        ],
        google_ads: [
          { action: "ads_campaigns", desc: "Lista campanhas ativas" },
          { action: "ads_performance", desc: "Performance das campanhas", params: ["startDate", "endDate"] }
        ]
      },
      example: {
        action: "ga_overview",
        params: { startDate: "7daysAgo", endDate: "today" }
      }
    };
  },

  // Google Analytics - Visao Geral
  async getAnalyticsOverview(params) {
    const startDate = params?.startDate || "7daysAgo";
    const endDate = params?.endDate || "today";

    // Usando a API do Google Analytics Data (GA4)
    const response = await this.google_analytics.runReport({
      property: `properties/${params?.propertyId || process.env.GA4_PROPERTY_ID}`,
      dateRanges: [{ startDate, endDate }],
      metrics: [
        { name: "sessions" },
        { name: "totalUsers" },
        { name: "screenPageViews" },
        { name: "averageSessionDuration" },
        { name: "bounceRate" }
      ]
    });

    return {
      success: true,
      period: { startDate, endDate },
      data: response.rows?.[0]?.metricValues || [],
      metrics: ["sessions", "totalUsers", "pageViews", "avgSessionDuration", "bounceRate"]
    };
  },

  // Google Analytics - Tempo Real
  async getAnalyticsRealtime(params) {
    const response = await this.google_analytics.runRealtimeReport({
      property: `properties/${params?.propertyId || process.env.GA4_PROPERTY_ID}`,
      metrics: [{ name: "activeUsers" }]
    });

    return {
      success: true,
      activeUsers: response.rows?.[0]?.metricValues?.[0]?.value || 0
    };
  },

  // Google Analytics - Relatorio Customizado
  async getAnalyticsReport(params) {
    const response = await this.google_analytics.runReport({
      property: `properties/${params?.propertyId || process.env.GA4_PROPERTY_ID}`,
      dateRanges: [{
        startDate: params?.startDate || "30daysAgo",
        endDate: params?.endDate || "today"
      }],
      dimensions: params?.dimensions?.map(d => ({ name: d })) || [{ name: "date" }],
      metrics: params?.metrics?.map(m => ({ name: m })) || [{ name: "sessions" }]
    });

    return {
      success: true,
      rows: response.rows || []
    };
  },

  // Google Ads - Listar Campanhas
  async getAdsCampaigns(params) {
    const customerId = params?.customerId || process.env.GOOGLE_ADS_CUSTOMER_ID;

    const response = await this.google_ads.search({
      customerId: customerId.replace(/-/g, ""),
      query: `
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.status != 'REMOVED'
        ORDER BY campaign.name
      `
    });

    return {
      success: true,
      campaigns: response.results?.map(r => ({
        id: r.campaign.id,
        name: r.campaign.name,
        status: r.campaign.status,
        budget: r.campaignBudget?.amountMicros / 1000000
      })) || []
    };
  },

  // Google Ads - Performance
  async getAdsPerformance(params) {
    const customerId = params?.customerId || process.env.GOOGLE_ADS_CUSTOMER_ID;
    const startDate = params?.startDate || "LAST_7_DAYS";

    const response = await this.google_ads.search({
      customerId: customerId.replace(/-/g, ""),
      query: `
        SELECT
          campaign.name,
          metrics.impressions,
          metrics.clicks,
          metrics.ctr,
          metrics.average_cpc,
          metrics.conversions,
          metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING ${startDate}
        AND campaign.status = 'ENABLED'
      `
    });

    return {
      success: true,
      period: startDate,
      campaigns: response.results?.map(r => ({
        name: r.campaign.name,
        impressions: r.metrics.impressions,
        clicks: r.metrics.clicks,
        ctr: (r.metrics.ctr * 100).toFixed(2) + "%",
        cpc: "R$ " + (r.metrics.averageCpc / 1000000).toFixed(2),
        conversions: r.metrics.conversions,
        cost: "R$ " + (r.metrics.costMicros / 1000000).toFixed(2)
      })) || []
    };
  }
});
