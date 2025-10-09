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
  block?: string | null;
  parcel?: string | null;
  subparcel?: string | null;
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
  avgPricePerSqm?: number | null;
  minPricePerSqm?: number | null;
  maxPricePerSqm?: number | null;
  antennaDistanceM?: number | null;
  shelterDistanceM?: number | null;
  rentEstimate?: number | null;
  buildingRights?: string | null;
  permitStatus?: string | null;
  permitDate?: string | null;
  assetStatus?: string | null;
  documents?: any[];
  assetId?: number | null;
  
  // GIS Collector Data Fields
  parcelArea?: number | null;
  parcelRegisteredArea?: number | null;
  parcelStatus?: string | null;
  parcelAccuracy?: number | null;
  blockArea?: number | null;
  blockRegisteredArea?: number | null;
  blockTotalParcels?: number | null;
  blockStatus?: string | null;
  blockLastUpdate?: number | null;
  totalPermits?: number | null;
  permitRequestNum?: string | null;
  permitPermissionNum?: string | null;
  permitBuildingNum?: string | null;
  permitHousingUnits?: number | null;
  permitCommercialArea?: number | null;
  permitResidentialArea?: number | null;
  permitResidentialUnits?: number | null;
  permitPublicArea?: number | null;
  permitParkingArea?: number | null;
  permitParkingUnits?: number | null;
  permitSmallApartments?: number | null;
  permitUnifiedHousingArea?: number | null;
  permitUnifiedHousingUnits?: number | null;
  permitAccessibleApartments?: number | null;
  permitPublicBuiltArea?: number | null;
  permitTotalArea?: number | null;
  permitMavatPlanNum?: string | null;
  permitParkingRoomsCalculated?: number | null;
  permitFullUtilization?: boolean | null;
  permitSubjectType?: string | null;
  permitProcess?: string | null;
  permitRightsNotification?: boolean | null;
  permitRepartition?: boolean | null;
  permitUrbanRenewal?: boolean | null;
  permitOpenRequestDate?: string | null;
  permitConstructionStartDate?: string | null;
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
  // Enhanced Planning Metrics
  buildingCoveragePct?: number | null;
  heightAnalysis?: {
    current_floors?: number | null;
    current_height_m?: number | null;
    allowed_floors?: number | null;
    allowed_height_m?: number | null;
    height_compliance?: string;
    confidence?: string;
  } | null;
  setbackAnalysis?: {
    violations?: string[];
    front_setback?: number | null;
    side_setback?: number | null;
    rear_setback?: number | null;
    confidence?: string;
  } | null;
  _meta?: Record<string, {
    source?: string;
    fetched_at?: string;
    url?: string;
  }>;
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
  snapshot?: {
    id: number;
    created_at: string;
    ppsqm?: number | null;
    payload: {
      blocks?: Array<any>;
      parcels?: Array<any>;
      permits?: Array<any>;
      rights?: Array<any>;
      shelters?: Array<any>;
      green?: Array<any>;
      noise?: Array<any>;
      x?: number;
      y?: number;
      [key: string]: any;
    };
  };
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
    pricePerSqm: row.price_per_sqm ?? null,
    pricePerSqmDisplay: row.pricePerSqmDisplay ?? row.price_per_sqm_display ?? null,
    description: row.description ?? null,
    images: row.images ?? row.photos ?? [],
    features: row.features ?? null,
    contactInfo: row.contactInfo ?? row.contact_info ?? null,
    block: row.block ?? null,
    parcel: row.parcel ?? null,
    subparcel: row.subparcel ?? null,
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
    avgPricePerSqm: row.avgPricePerSqm ?? row.avg_price_per_sqm ?? null,
    minPricePerSqm: row.minPricePerSqm ?? row.min_price_per_sqm ?? null,
    maxPricePerSqm: row.maxPricePerSqm ?? row.max_price_per_sqm ?? null,
    antennaDistanceM: row.antennaDistanceM ?? row.antenna_distance_m ?? null,
    shelterDistanceM: row.shelterDistanceM ?? row.shelter_distance_m ?? null,
    rentEstimate: row.rentEstimate ?? row.rent_estimate ?? null,
    buildingRights: row.buildingRights ?? row.building_rights ?? null,
    permitStatus: row.permitStatus ?? row.permit_status ?? null,
    permitDate: row.permitDate ?? row.permit_date ?? null,
    assetStatus: row.assetStatus ?? row.asset_status ?? row.status ?? null,
    documents: Array.isArray(row.documents) ? row.documents : (row.meta?.documents || []),
    assetId: row.assetId ?? row.asset_id ?? null,
    
    // GIS Collector Data Fields
    parcelArea: row.parcelArea ?? row.parcel_area ?? null,
    parcelRegisteredArea: row.parcelRegisteredArea ?? row.parcel_registered_area ?? null,
    parcelStatus: row.parcelStatus ?? row.parcel_status ?? null,
    parcelAccuracy: row.parcelAccuracy ?? row.parcel_accuracy ?? null,
    blockArea: row.blockArea ?? row.block_area ?? null,
    blockRegisteredArea: row.blockRegisteredArea ?? row.block_registered_area ?? null,
    blockTotalParcels: row.blockTotalParcels ?? row.block_total_parcels ?? null,
    blockStatus: row.blockStatus ?? row.block_status ?? null,
    blockLastUpdate: row.blockLastUpdate ?? row.block_last_update ?? null,
    totalPermits: row.totalPermits ?? row.total_permits ?? null,
    permitRequestNum: row.permitRequestNum ?? row.permit_request_num ?? null,
    permitPermissionNum: row.permitPermissionNum ?? row.permit_permission_num ?? null,
    permitBuildingNum: row.permitBuildingNum ?? row.permit_building_num ?? null,
    permitHousingUnits: row.permitHousingUnits ?? row.permit_housing_units ?? null,
    permitCommercialArea: row.permitCommercialArea ?? row.permit_commercial_area ?? null,
    permitResidentialArea: row.permitResidentialArea ?? row.permit_residential_area ?? null,
    permitResidentialUnits: row.permitResidentialUnits ?? row.permit_residential_units ?? null,
    permitPublicArea: row.permitPublicArea ?? row.permit_public_area ?? null,
    permitParkingArea: row.permitParkingArea ?? row.permit_parking_area ?? null,
    permitParkingUnits: row.permitParkingUnits ?? row.permit_parking_units ?? null,
    permitSmallApartments: row.permitSmallApartments ?? row.permit_small_apartments ?? null,
    permitUnifiedHousingArea: row.permitUnifiedHousingArea ?? row.permit_unified_housing_area ?? null,
    permitUnifiedHousingUnits: row.permitUnifiedHousingUnits ?? row.permit_unified_housing_units ?? null,
    permitAccessibleApartments: row.permitAccessibleApartments ?? row.permit_accessible_apartments ?? null,
    permitPublicBuiltArea: row.permitPublicBuiltArea ?? row.permit_public_built_area ?? null,
    permitTotalArea: row.permitTotalArea ?? row.permit_total_area ?? null,
    permitMavatPlanNum: row.permitMavatPlanNum ?? row.permit_mavat_plan_num ?? null,
    permitParkingRoomsCalculated: row.permitParkingRoomsCalculated ?? row.permit_parking_rooms_calculated ?? null,
    permitFullUtilization: row.permitFullUtilization ?? row.permit_full_utilization ?? null,
    permitSubjectType: row.permitSubjectType ?? row.permit_subject_type ?? null,
    permitProcess: row.permitProcess ?? row.permit_process ?? null,
    permitRightsNotification: row.permitRightsNotification ?? row.permit_rights_notification ?? null,
    permitRepartition: row.permitRepartition ?? row.permit_repartition ?? null,
    permitUrbanRenewal: row.permitUrbanRenewal ?? row.permit_urban_renewal ?? null,
    permitOpenRequestDate: row.permitOpenRequestDate ?? row.permit_open_request_date ?? null,
    permitConstructionStartDate: row.permitConstructionStartDate ?? row.permit_construction_start_date ?? null,
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
    // Enhanced Planning Metrics
    buildingCoveragePct: row.buildingCoveragePct ?? row.building_coverage_pct ?? null,
    heightAnalysis: row.heightAnalysis ?? row.height_analysis ?? null,
    setbackAnalysis: row.setbackAnalysis ?? row.setback_analysis ?? null,
    _meta: row._meta ?? undefined,
    attribution: row.attribution ?? undefined,
    recent_contributions: row.recent_contributions ?? undefined,
    snapshot: row.snapshot ?? undefined,
  };
}
