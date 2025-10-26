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
  subparcelArea?: number | null; // subparcel area from Tabu
  builtArea?: number | null; // built area from Tabu
  balconyArea?: number | null;
  parkingSpaces?: number | null;
  price?: number | null;
  pricePerSqm?: number | null;
  pricePerSqmDisplay?: number | null;
  description?: string | null;
  images?: string[];
  photos?: string[];
  features?: string[] | null;
  contactInfo?: {
    agent?: string | null;
    phone?: string | null;
    email?: string | null;
    name?: string | null;
    brokerPhone?: string | null;
  } | null;
  block?: string | null;
  parcel?: string | null;
  subparcel?: string | null;
  lat?: number | null;
  lon?: number | null;
  normalizedAddress?: string | null;
  buildingType?: string | null;
  isCommercial?: boolean | null;
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
  primaryListing?: {
    id?: string | number | null;
    source?: string | null;
    title?: string | null;
    price?: number | null;
    address?: string | null;
    rooms?: number | null;
    roomsDisplay?: string | null;
    size?: number | null;
    propertyType?: string | null;
    listingType?: string | null;
    adType?: string | null;
    description?: string | null;
    floor?: string | number | null;
    contactName?: string | null;
    contactPhone?: string | null;
    contactInfo?: {
      name?: string | null;
      phone?: string | null;
      brokerPhone?: string | null;
      email?: string | null;
    } | null;
    recentDeal?: boolean | null;
    photos?: string[];
    videoUrl?: string | null;
    url?: string | null;
    features?: string[] | null;
    datePosted?: string | null;
  } | null;
  listingType?: string | null;
  adType?: string | null;
  contactName?: string | null;
  contactPhone?: string | null;
  recentDeal?: boolean | null;
  videoUrl?: string | null;
  
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
  const ensureStringArray = (value: unknown): string[] =>
    Array.isArray(value)
      ? value.filter((item): item is string => typeof item === 'string' && item.length > 0)
      : [];

  const parseNumeric = (input: unknown): number | null => {
    if (input === null || input === undefined) {
      return null;
    }
    if (typeof input === 'number') {
      return Number.isFinite(input) ? input : null;
    }
    if (typeof input === 'bigint') {
      return Number(input);
    }
    if (typeof input === 'string') {
      const trimmed = input.trim();
      if (!trimmed) {
        return null;
      }
      const normalized = trimmed.replace(/[^0-9.\-]/g, '');
      if (!normalized) {
        return null;
      }
      const parsed = Number(normalized);
      return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
  };

  const coerceString = (value: unknown): string | null => {
    if (value === null || value === undefined) {
      return null;
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed.length ? trimmed : null;
    }
    if (typeof value === 'number' || typeof value === 'bigint') {
      return String(value);
    }
    return null;
  };

  const sanitizeRoomsDisplay = (rooms: number | null, display: unknown): string | null => {
    if (typeof display === 'string') {
      const trimmed = display.trim();
      if (trimmed.length) {
        return trimmed;
      }
    }
    if (rooms === null || rooms === undefined || Number.isNaN(rooms)) {
      return null;
    }
    const numericRooms = Number(rooms);
    if (!Number.isFinite(numericRooms)) {
      return null;
    }
    const formatted = Number.isInteger(numericRooms)
      ? numericRooms.toString()
      : Number(numericRooms.toFixed(1)).toString();
    return `${formatted} חדרים`;
  };

  const sanitizeFeatures = (value: unknown): string[] => {
    return Array.from(
      new Set(
        ensureStringArray(value).map(feature => feature.trim()).filter(Boolean)
      )
    );
  };

  const coerceFloorValue = (value: unknown): string | number | null => {
    if (value === null || value === undefined) {
      return null;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed.length ? trimmed : null;
    }
    if (typeof value === 'bigint') {
      return Number(value);
    }
    return null;
  };

  const coerceDateString = (value: unknown): string | null => {
    if (value === null || value === undefined) {
      return null;
    }
    if (value instanceof Date) {
      return Number.isNaN(value.getTime()) ? null : value.toISOString();
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed.length ? trimmed : null;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      const epochMillis = value > 1e12 ? value : value * 1000;
      const date = new Date(epochMillis);
      return Number.isNaN(date.getTime()) ? null : date.toISOString();
    }
    return null;
  };

  const normalizeListing = (listing: any) => {
    if (!listing || typeof listing !== 'object') {
      return null;
    }

    const rawContact = listing.contactInfo ?? listing.contact_info;
    const baseContact =
      rawContact && typeof rawContact === 'object'
        ? { ...rawContact }
        : {};

    const contactName =
      listing.contactName ?? listing.contact_name ?? baseContact.name ?? null;
    const contactPhone =
      listing.contactPhone ??
      listing.contact_phone ??
      baseContact.phone ??
      baseContact.brokerPhone ??
      null;

    if (contactName != null) {
      baseContact.name = contactName;
    }
    if (contactPhone != null) {
      baseContact.phone = contactPhone;
    }

    const listingContactInfo = Object.values(baseContact).some(
      value => value != null && value !== ''
    )
      ? baseContact
      : null;

    const photos = Array.from(
      new Set([
        ...ensureStringArray(listing.photos),
        ...ensureStringArray(listing.images),
      ])
    );

    const videoUrl =
      listing.videoUrl ?? listing.video_url ?? listing.video ?? null;

    let recentDeal: boolean | null = null;
    if (typeof listing.recentDeal === 'boolean') {
      recentDeal = listing.recentDeal;
    } else if (typeof listing.recent_deal === 'boolean') {
      recentDeal = listing.recent_deal;
    }

    const price =
      parseNumeric(
        listing.price ??
        listing.listing_price ??
        listing.priceValue ??
        listing.price_value
      );

    const size =
      parseNumeric(
        listing.size ??
        listing.area ??
        listing.squareMeters ??
        listing.square_meters
      );

    const rooms =
      parseNumeric(
        listing.rooms ??
        listing.rooms_count ??
        listing.roomsCount
      );

    const roomsDisplay = sanitizeRoomsDisplay(
      rooms,
      listing.roomsDisplay ?? listing.rooms_display ?? listing.roomsText ?? listing.rooms_text
    );

    const propertyType =
      coerceString(listing.propertyType ?? listing.property_type);

    const description =
      coerceString(
        listing.description ??
        listing.details ??
        listing.about ??
        listing.text ??
        listing.body
      );

    const floor = coerceFloorValue(
      listing.floor ??
      listing.floorDisplay ??
      listing.floor_display ??
      listing.floorLabel ??
      listing.floor_label
    );

    const features = sanitizeFeatures(
      listing.features ??
      listing.features_list ??
      listing.feature_list ??
      listing.tags
    );

    const datePosted = coerceDateString(
      listing.datePosted ??
      listing.date_posted ??
      listing.postedAt ??
      listing.posted_at ??
      listing.scrapedAt ??
      listing.scraped_at ??
      listing.fetched_at
    );

    const address =
      coerceString(
        listing.address ??
        listing.location ??
        listing.fullAddress ??
        listing.full_address
      );

    const title =
      coerceString(
        listing.title ??
        listing.heading ??
        listing.headline ??
        listing.name
      );

    const url = coerceString(listing.url ?? listing.link ?? listing.listingUrl ?? listing.listing_url);

    return {
      id: listing.id ?? listing.external_id ?? null,
      source: coerceString(listing.source) ?? null,
      title,
      price,
      address,
      rooms: rooms ?? null,
      roomsDisplay: roomsDisplay ?? null,
      size,
      propertyType,
      listingType: listing.listingType ?? listing.listing_type ?? null,
      adType: listing.adType ?? listing.ad_type ?? null,
      description,
      floor,
      contactName: contactName ?? null,
      contactPhone: contactPhone ?? null,
      contactInfo: listingContactInfo,
      recentDeal,
      photos,
      videoUrl,
      url,
      features: features.length ? features : null,
      datePosted,
    };
  };

  const primaryListing = normalizeListing(row.primaryListing ?? row.primary_listing);

  const rawContactInfo = row.contactInfo ?? row.contact_info;
  const baseContactInfo =
    rawContactInfo && typeof rawContactInfo === 'object'
      ? { ...rawContactInfo }
      : {};

  const listingType =
    row.listingType ?? row.listing_type ?? primaryListing?.listingType ?? null;

  const adType =
    row.adType ?? row.ad_type ?? primaryListing?.adType ?? null;

  const normalizedListingTypeValue =
    typeof listingType === 'string' ? listingType.toLowerCase() : null;
  const primaryListingTypeValue =
    typeof primaryListing?.listingType === 'string'
      ? primaryListing.listingType.toLowerCase()
      : null;

  const rawIsCommercial = (row as any).isCommercial ?? (row as any).is_commercial;
  let isCommercial: boolean | null = null;
  if (typeof rawIsCommercial === 'boolean') {
    isCommercial = rawIsCommercial;
  } else if (typeof rawIsCommercial === 'string') {
    const normalized = rawIsCommercial.trim().toLowerCase();
    if (normalized === 'true') {
      isCommercial = true;
    } else if (normalized === 'false') {
      isCommercial = false;
    }
  } else if (
    normalizedListingTypeValue === 'commercial' ||
    primaryListingTypeValue === 'commercial'
  ) {
    isCommercial = true;
  }

  const contactName =
    row.contactName ??
    row.contact_name ??
    primaryListing?.contactName ??
    baseContactInfo.name ??
    null;

  const contactPhone =
    row.contactPhone ??
    row.contact_phone ??
    primaryListing?.contactPhone ??
    baseContactInfo.phone ??
    baseContactInfo.brokerPhone ??
    null;

  const recentDeal =
    row.recentDeal ?? row.recent_deal ?? primaryListing?.recentDeal ?? null;

  const videoUrl =
    row.videoUrl ?? row.video_url ?? primaryListing?.videoUrl ?? null;

  if (contactName != null) {
    baseContactInfo.name = contactName;
  }
  if (contactPhone != null) {
    baseContactInfo.phone = contactPhone;
  }
  if (
    baseContactInfo.brokerPhone == null &&
    primaryListing?.contactInfo?.brokerPhone
  ) {
    baseContactInfo.brokerPhone = primaryListing.contactInfo.brokerPhone;
  }
  if (baseContactInfo.email == null && primaryListing?.contactInfo?.email) {
    baseContactInfo.email = primaryListing.contactInfo.email;
  }

  const hasContactInfo = Object.values(baseContactInfo).some(
    value => value != null && value !== ''
  );

  const images = Array.from(
    new Set([
      ...ensureStringArray(row.images),
      ...ensureStringArray(row.photos),
      ...(primaryListing?.photos ?? []),
    ])
  );

  const priceValue =
    parseNumeric(row.price ?? row.price_value ?? row.priceValue) ??
    primaryListing?.price ??
    null;

  const pricePerSqmDirect = parseNumeric(
    row.pricePerSqm ??
    row.price_per_sqm ??
    row.pricePerSqmDisplay ??
    row.price_per_sqm_display
  );

  const rowAreaCandidate = row.area ?? row.netSqm ?? row.net_sqm;
  const areaValue = parseNumeric(rowAreaCandidate) ?? primaryListing?.size ?? null;

  const computedPricePerSqm =
    pricePerSqmDirect ??
    (priceValue != null && areaValue
      ? Math.round(priceValue / areaValue)
      : null);

  const descriptionValue =
    coerceString(row.description ?? row.summary ?? row.details) ??
    primaryListing?.description ??
    null;

  const rowRoomsCandidate = row.rooms ?? row.rooms_count ?? row.roomsCount;
  const normalizedRowRooms = parseNumeric(rowRoomsCandidate);
  const normalizedBedrooms = parseNumeric(row.bedrooms ?? row.bedrooms_count ?? row.bedroomsCount);
  const roomsValue =
    normalizedRowRooms ??
    normalizedBedrooms ??
    primaryListing?.rooms ??
    null;

  const listingFloor = primaryListing?.floor;
  const floorValue =
    row.floor ??
    parseNumeric(row.floorNumber ?? row.floor_number) ??
    (typeof listingFloor === 'number'
      ? listingFloor
      : parseNumeric(listingFloor));

  const buildingTypeValue =
    coerceString(row.buildingType ?? row.building_type) ??
    primaryListing?.propertyType ??
    null;

  const addressValue =
    coerceString(row.address) ??
    primaryListing?.address ??
    null;

  const normalizedAddressValue =
    coerceString(row.normalizedAddress ?? row.normalized_address) ??
    addressValue;

  const combinedFeatures = (() => {
    const base = ensureStringArray(row.features);
    const listing = Array.isArray(primaryListing?.features)
      ? primaryListing?.features ?? []
      : [];
    const merged = [...base, ...listing].map(feature => (typeof feature === 'string' ? feature.trim() : '')).filter(Boolean);
    return merged.length ? Array.from(new Set(merged)) : null;
  })();

  const typeValue = determineAssetType(row) ?? primaryListing?.propertyType ?? null;

  const bedroomsValue =
    row.bedrooms != null
      ? parseNumeric(row.bedrooms)
      : normalizedBedrooms;

  return {
    id: Number(row.id ?? row.assetId ?? row.external_id),
    address: addressValue ?? null,
    city: row.city ?? null,
    neighborhood: row.neighborhood ?? null,
    street: row.street ?? null,
    number: row.number ?? null,
    apartment: row.apartment ?? null,
    type: typeValue,
    bedrooms: bedroomsValue ?? null,
    rooms: roomsValue ?? null,
    bathrooms: row.bathrooms ?? null,
    area: areaValue ?? null,
    totalArea: row.totalArea ?? row.totalSqm ?? null,
    subparcelArea: row.subparcelArea ?? row.subparcel_area ?? null,
    builtArea: row.builtArea ?? row.built_area ?? null,
    balconyArea: row.balconyArea ?? row.balcony_area ?? null,
    parkingSpaces: row.parkingSpaces ?? row.parking_spaces ?? null,
    price: priceValue,
    pricePerSqm: computedPricePerSqm,
    pricePerSqmDisplay: pricePerSqmDirect ?? computedPricePerSqm,
    description: descriptionValue,
    images,
    photos: images,
    features: combinedFeatures,
    contactInfo: hasContactInfo ? baseContactInfo : null,
    block: row.block ?? null,
    parcel: row.parcel ?? null,
    subparcel: row.subparcel ?? null,
    lat: row.lat ?? null,
    lon: row.lon ?? null,
    normalizedAddress: normalizedAddressValue ?? null,
    buildingType: buildingTypeValue,
    isCommercial,
    floor: floorValue ?? null,
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
    primaryListing,
    listingType,
    adType,
    contactName,
    contactPhone,
    recentDeal,
    videoUrl,
    
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
