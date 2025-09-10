export type Asset = {
  id: number;
  address?: string | null;
  city?: string | null;
  neighborhood?: string | null;
  street?: string | null;
  number?: number | null;
  apartment?: string | null;
  type?: string | null;
  bedrooms?: number | null;
  rooms?: number | null;
  bathrooms?: number | null;
  area?: number | null; // net sqm
  totalArea?: number | null; // total sqm
  balconyArea?: number | null;
  parkingSpaces?: number | null;
  price?: number | null;
  pricePerSqm?: number | null;
  pricePerSqmDisplay?: number | null;
  description?: string | null;
  images?: string[];
  features?: string[] | null;
  contactInfo?: {
    agent?: string | null;
    phone?: string | null;
    email?: string | null;
  } | null;
  gush?: string | null;
  helka?: string | null;
  subhelka?: string | null;
  lat?: number | null;
  lon?: number | null;
  normalizedAddress?: string | null;
  buildingType?: string | null;
  floor?: number | null;
  totalFloors?: number | null;
  storageRoom?: boolean | null;
  elevator?: boolean | null;
  airConditioning?: boolean | null;
  furnished?: boolean | null;
  renovated?: boolean | null;
  yearBuilt?: number | null;
  lastRenovation?: number | null;
  deltaVsAreaPct?: number | null;
  domPercentile?: number | null;
  competition1km?: string | null;
  zoning?: string | null;
  riskFlags?: string[] | null;
  priceGapPct?: number | null;
  expectedPriceRange?: string | null;
  remainingRightsSqm?: number | null;
  program?: string | null;
  lastPermitQ?: string | null;
  noiseLevel?: number | null;
  greenWithin300m?: boolean | null;
  schoolsWithin500m?: boolean | null;
  modelPrice?: number | null;
  confidencePct?: number | null;
  capRatePct?: number | null;
  antennaDistanceM?: number | null;
  shelterDistanceM?: number | null;
  rentEstimate?: number | null;
  buildingRights?: string | null;
  permitStatus?: string | null;
  permitDate?: string | null;
  assetStatus?: string | null;
  documents?: any[];
  assetId?: number | null;
  sources?: string[] | null;
  primarySource?: string | null;
  permitDateDisplay?: string | null;
  permitStatusDisplay?: string | null;
  permitDetails?: string | null;
  permitMainArea?: number | null;
  permitServiceArea?: number | null;
  permitApplicant?: string | null;
  permitDocUrl?: string | null;
  mainRightsSqm?: number | null;
  serviceRightsSqm?: number | null;
  additionalPlanRights?: string | null;
  planStatus?: string | null;
  planActive?: boolean | null;
  publicObligations?: string | null;
  publicTransport?: string | null;
  openSpacesNearby?: string | null;
  publicBuildings?: string | null;
  parking?: string | null;
  nearbyProjects?: string | null;
  rightsUsagePct?: number | null;
  legalRestrictions?: string | null;
  urbanRenewalPotential?: string | null;
  bettermentLevy?: string | null;
  _meta?: Record<string, any>;
  attribution?: {
    created_by?: {
      id: number;
      email: string;
      name: string;
    };
    last_updated_by?: {
      id: number;
      email: string;
      name: string;
    };
  };
  recent_contributions?: Array<{
    id: number;
    user: {
      email: string;
      name: string;
    };
    type: string;
    type_display: string;
    field_name?: string;
    description?: string;
    source?: string;
    created_at: string;
  }>;
};

export function determineAssetType(asset: any): string | null {
  return asset?.propertyType || asset?.property_type || asset?.type || null;
}

export function normalizeFromBackend(row: any): Asset {
  return {
    id: Number(row.id ?? row.assetId ?? row.external_id),
    address: row.address ?? null,
    city: row.city ?? null,
    neighborhood: row.neighborhood ?? null,
    street: row.street ?? null,
    number: row.number ?? null,
    apartment: row.apartment ?? null,
    type: determineAssetType(row),
    bedrooms: row.bedrooms ?? null,
    rooms: row.rooms ?? row.bedrooms ?? null,
    bathrooms: row.bathrooms ?? null,
    area: row.area ?? row.netSqm ?? null,
    totalArea: row.totalArea ?? row.totalSqm ?? null,
    balconyArea: row.balconyArea ?? row.balcony_area ?? null,
    parkingSpaces: row.parkingSpaces ?? row.parking_spaces ?? null,
    price: row.price ?? null,
    pricePerSqm: row.pricePerSqm ?? row.ppsqm ?? null,
    pricePerSqmDisplay: row.pricePerSqmDisplay ?? row.price_per_sqm_display ?? null,
    description: row.description ?? null,
    images: row.images ?? row.photos ?? [],
    features: row.features ?? null,
    contactInfo: row.contactInfo ?? row.contact_info ?? null,
    gush: row.gush ?? null,
    helka: row.helka ?? null,
    subhelka: row.subhelka ?? null,
    lat: row.lat ?? null,
    lon: row.lon ?? null,
    normalizedAddress: row.normalizedAddress ?? row.normalized_address ?? null,
    buildingType: row.buildingType ?? row.building_type ?? null,
    floor: row.floor ?? null,
    totalFloors: row.totalFloors ?? row.total_floors ?? null,
    storageRoom: row.storageRoom ?? row.storage_room ?? null,
    elevator: row.elevator ?? null,
    airConditioning: row.airConditioning ?? row.air_conditioning ?? null,
    furnished: row.furnished ?? null,
    renovated: row.renovated ?? null,
    yearBuilt: row.yearBuilt ?? row.year_built ?? null,
    lastRenovation: row.lastRenovation ?? row.last_renovation ?? null,
    deltaVsAreaPct: row.deltaVsAreaPct ?? row.delta_vs_area_pct ?? null,
    domPercentile: row.domPercentile ?? row.dom_percentile ?? null,
    competition1km: row.competition1km ?? row.competition_1km ?? null,
    zoning: row.zoning ?? null,
    riskFlags: row.riskFlags ?? row.risk_flags ?? null,
    priceGapPct: row.priceGapPct ?? row.price_gap_pct ?? null,
    expectedPriceRange: row.expectedPriceRange ?? row.expected_price_range ?? null,
    remainingRightsSqm: row.remainingRightsSqm ?? row.remaining_rights_sqm ?? null,
    program: row.program ?? null,
    lastPermitQ: row.lastPermitQ ?? row.last_permit_q ?? null,
    noiseLevel: row.noiseLevel ?? row.noise_level ?? null,
    greenWithin300m: row.greenWithin300m ?? row.green_within_300m ?? null,
    schoolsWithin500m: row.schoolsWithin500m ?? row.schools_within_500m ?? null,
    modelPrice: row.modelPrice ?? row.model_price ?? null,
    confidencePct: row.confidencePct ?? row.confidence_pct ?? null,
    capRatePct: row.capRatePct ?? row.cap_rate_pct ?? null,
    antennaDistanceM: row.antennaDistanceM ?? row.antenna_distance_m ?? null,
    shelterDistanceM: row.shelterDistanceM ?? row.shelter_distance_m ?? null,
    rentEstimate: row.rentEstimate ?? row.rent_estimate ?? null,
    buildingRights: row.buildingRights ?? row.building_rights ?? null,
    permitStatus: row.permitStatus ?? row.permit_status ?? null,
    permitDate: row.permitDate ?? row.permit_date ?? null,
    assetStatus: row.assetStatus ?? row.asset_status ?? row.status ?? null,
    documents: row.documents ?? [],
    assetId: row.assetId ?? row.asset_id ?? null,
    sources: row.sources ?? null,
    primarySource: row.primarySource ?? row.primary_source ?? null,
    permitDateDisplay: row.permitDateDisplay ?? row.permit_date_display ?? null,
    permitStatusDisplay: row.permitStatusDisplay ?? row.permit_status_display ?? null,
    permitDetails: row.permitDetails ?? row.permit_details ?? null,
    permitMainArea: row.permitMainArea ?? row.permit_main_area ?? null,
    permitServiceArea: row.permitServiceArea ?? row.permit_service_area ?? null,
    permitApplicant: row.permitApplicant ?? row.permit_applicant ?? null,
    permitDocUrl: row.permitDocUrl ?? row.permit_doc_url ?? null,
    mainRightsSqm: row.mainRightsSqm ?? row.main_rights_sqm ?? null,
    serviceRightsSqm: row.serviceRightsSqm ?? row.service_rights_sqm ?? null,
    additionalPlanRights: row.additionalPlanRights ?? row.additional_plan_rights ?? null,
    planStatus: row.planStatus ?? row.plan_status ?? null,
    planActive: row.planActive ?? row.plan_active ?? null,
    publicObligations: row.publicObligations ?? row.public_obligations ?? null,
    publicTransport: row.publicTransport ?? row.public_transport ?? null,
    openSpacesNearby: row.openSpacesNearby ?? row.open_spaces_nearby ?? null,
    publicBuildings: row.publicBuildings ?? row.public_buildings ?? null,
    parking: row.parking ?? null,
    nearbyProjects: row.nearbyProjects ?? row.nearby_projects ?? null,
    rightsUsagePct: row.rightsUsagePct ?? row.rights_usage_pct ?? null,
    legalRestrictions: row.legalRestrictions ?? row.legal_restrictions ?? null,
    urbanRenewalPotential: row.urbanRenewalPotential ?? row.urban_renewal_potential ?? null,
    bettermentLevy: row.bettermentLevy ?? row.betterment_levy ?? null,
    _meta: row._meta ?? undefined,
    attribution: row.attribution ?? undefined,
    recent_contributions: row.recent_contributions ?? undefined,
  };
}
