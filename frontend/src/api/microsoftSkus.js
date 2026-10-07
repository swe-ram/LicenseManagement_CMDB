// Microsoft 365 SKU Catalog & Normalization Mapping

export const MS_SKU_METADATA = {
  O365_BUSINESS_PREMIUM: {
    displayName: 'Microsoft 365 Business Premium',
    category: 'Business Suite',
    description: 'Comprehensive productivity suite with advanced security & device management.',
    unitCostAnnual: 264.0, // $22/seat/month
    badgeColor: 'primary',
    icon: 'ShieldCheck',
  },
  O365_BUSINESS_ESSENTIALS: {
    displayName: 'Microsoft 365 Business Basic',
    category: 'Productivity & Cloud',
    description: 'Cloud services including web & mobile Office apps, Teams, Exchange & SharePoint.',
    unitCostAnnual: 72.0, // $6/seat/month
    badgeColor: 'info',
    icon: 'Cloud',
  },
  ENTERPRISEPACK: {
    displayName: 'Office 365 E3 Enterprise',
    category: 'Enterprise Cloud',
    description: 'Enterprise-grade productivity apps with compliance and data protection.',
    unitCostAnnual: 276.0, // $23/seat/month
    badgeColor: 'primary',
    icon: 'Briefcase',
  },
  EXCHANGEENTERPRISE: {
    displayName: 'Exchange Online (Plan 2)',
    category: 'Messaging & Email',
    description: 'Enterprise email, calendaring, unlimited archiving, and DLP compliance.',
    unitCostAnnual: 96.0, // $8/seat/month
    badgeColor: 'warning',
    icon: 'Mail',
  },
  'Teams_Premium_(for_Departments)': {
    displayName: 'Microsoft Teams Premium',
    category: 'Collaboration & Meetings',
    description: 'Advanced AI meeting summaries, customized branding, and webinar features.',
    unitCostAnnual: 120.0, // $10/seat/month
    badgeColor: 'purple',
    icon: 'Video',
  },
  POWER_BI_PRO: {
    displayName: 'Microsoft Power BI Pro',
    category: 'Analytics & BI',
    description: 'Self-service analytics to visualize data and share interactive reports.',
    unitCostAnnual: 120.0, // $10/seat/month
    badgeColor: 'warning',
    icon: 'BarChart2',
  },
  POWER_BI_STANDARD: {
    displayName: 'Microsoft Power BI (Standard / Free)',
    category: 'Analytics & BI',
    description: 'Standard access for personal analytics and report viewing.',
    unitCostAnnual: 0.0,
    badgeColor: 'neutral',
    icon: 'PieChart',
  },
  FLOW_FREE: {
    displayName: 'Microsoft Power Automate (Free)',
    category: 'Automation & Workflows',
    description: 'Workflow automation across business applications and services.',
    unitCostAnnual: 0.0,
    badgeColor: 'neutral',
    icon: 'Zap',
  },
  POWERAPPS_DEV: {
    displayName: 'Microsoft Power Apps for Developer',
    category: 'Developer & Sandbox',
    description: 'Dedicated sandbox environment for testing Power Apps and Dataverse.',
    unitCostAnnual: 0.0,
    badgeColor: 'info',
    icon: 'Code',
  },
  THREAT_INTELLIGENCE: {
    displayName: 'Microsoft Defender Threat Intelligence',
    category: 'Cybersecurity & Identity',
    description: 'Direct visibility into threat actor infrastructure and proactive defenses.',
    unitCostAnnual: 600.0, // $50/seat/month
    badgeColor: 'danger',
    icon: 'ShieldAlert',
  },
  Dynamics_365_Sales_Premium_Viral_Trial: {
    displayName: 'Dynamics 365 Sales Premium (Trial)',
    category: 'CRM & Sales',
    description: 'Sales automation with predictive forecasting and relationship intelligence.',
    unitCostAnnual: 1620.0, // $135/seat/month
    badgeColor: 'success',
    icon: 'TrendingUp',
  },
  Dynamics_365_Customer_Service_Enterprise_viral_trial: {
    displayName: 'Dynamics 365 Customer Service Enterprise',
    category: 'Customer Service & Support',
    description: 'Omnichannel customer support, case routing, and agent collaboration.',
    unitCostAnnual: 1260.0, // $105/seat/month
    badgeColor: 'info',
    icon: 'Headphones',
  },
  Power_Pages_vTrial_for_Makers: {
    displayName: 'Microsoft Power Pages Maker Trial',
    category: 'Low-Code Web Apps',
    description: 'Secure, low-code platform for building external business web portals.',
    unitCostAnnual: 0.0,
    badgeColor: 'neutral',
    icon: 'Globe',
  },
  AX7_USER_TRIAL: {
    displayName: 'Dynamics 365 Finance & Operations',
    category: 'Enterprise ERP',
    description: 'Global enterprise financials, supply chain, and manufacturing management.',
    unitCostAnnual: 2160.0, // $180/seat/month
    badgeColor: 'purple',
    icon: 'Layers',
  },
  PROJECT_MADEIRA_PREVIEW_IW_SKU: {
    displayName: 'Dynamics 365 Business Central',
    category: 'Cloud ERP',
    description: 'All-in-one business management for SMB finance, sales, service, and operations.',
    unitCostAnnual: 840.0, // $70/seat/month
    badgeColor: 'primary',
    icon: 'Database',
  },
  CCIBOTS_PRIVPREV_VIRAL: {
    displayName: 'Microsoft Copilot Studio / Bot Services',
    category: 'AI & Copilot Studio',
    description: 'Custom AI conversational copilots with natural language understanding.',
    unitCostAnnual: 2400.0, // $200/month capacity
    badgeColor: 'purple',
    icon: 'Bot',
  },
};

/**
 * Returns formatted metadata for any Microsoft SKU part number.
 */
export const getMicrosoftSkuMeta = (skuPartNumber) => {
  if (!skuPartNumber) {
    return {
      displayName: 'Microsoft 365 License',
      category: 'Cloud Services',
      description: 'Enterprise Microsoft 365 subscription SKU.',
      unitCostAnnual: 120.0,
      badgeColor: 'primary',
    };
  }

  const meta = MS_SKU_METADATA[skuPartNumber];
  if (meta) return meta;

  // Pretty-print unknown SKU names (replace underscores with spaces)
  const cleaned = skuPartNumber
    .replace(/_/g, ' ')
    .replace(/trial/gi, 'Trial')
    .replace(/sku/gi, '')
    .trim();

  return {
    displayName: cleaned,
    category: 'Microsoft 365 Service',
    description: `Microsoft 365 commercial SKU (${skuPartNumber}).`,
    unitCostAnnual: 60.0,
    badgeColor: 'neutral',
  };
};

/**
 * Normalizes a raw Microsoft 365 license item into the portal standard schema.
 */
export const normalizeMicrosoftLicense = (raw, index = 0) => {
  const skuPart = raw.sku_part_number || raw.product || 'M365';
  const meta = getMicrosoftSkuMeta(skuPart);

  const purchased = Number(raw.purchased_quantity || 0);
  const assigned = Number(raw.assigned_quantity || 0);
  const available = Number(raw.available_quantity != null ? raw.available_quantity : Math.max(0, purchased - assigned));
  const used = assigned;

  // Calculate annual commercial spend
  const cost = Math.round(assigned * meta.unitCostAnnual);

  return {
    license_id: raw.sku_id || `ms-${index + 1}`,
    sku_id: raw.sku_id,
    db_license_id: raw.id || raw.license_id,
    license_name: meta.displayName,
    raw_sku_part_number: skuPart,
    product: meta.displayName,
    product_code: skuPart,
    license_type: meta.category,
    application_name: 'Microsoft 365',
    vendor: 'Microsoft',
    total_quantity: purchased,
    allocated_quantity: assigned,
    used_quantity: used,
    available_quantity: available,
    cost_amount: cost,
    unit_cost: meta.unitCostAnnual,
    currency: 'USD',
    billing_frequency: 'annual',
    status: (raw.capability_status || 'Enabled').toLowerCase() === 'enabled' ? 'active' : 'suspended',
    purchase_date: '2024-01-01',
    start_date: '2024-01-01',
    expiry_date: '2026-12-31',
    auto_renew: true,
    source_system: 'Microsoft Graph API (Live Sync)',
    service_plans_count: Array.isArray(raw.service_plans) ? raw.service_plans.length : 0,
    service_plans: raw.service_plans || [],
    description: meta.description,
    badgeColor: meta.badgeColor,
  };
};
