/**
 * Centralized Internationalization (i18n) for AquaMediAI Farmer View
 * Supported Languages: English (en), हिन्दी (hi), ગુજરાતી (gu)
 *
 * All translations are localized for agricultural clarity and simplicity.
 * No external translation APIs are used.
 */

export type Language = 'en' | 'hi' | 'gu' | 'mr';

export interface Translations {
  // App branding & header
  appTitle: string;
  appSubtitle: string;
  farmerView: string;
  expertView: string;
  waterConflictMonitor: string;
  waterConflictsFound: string;
  mostUrgentIssue: string;
  waterShortage: string;
  availableWaterVsFarmDemand: string;
  overlappingIrrigationSchedules: string;
  highWaterPriority: string;
  farmsInvolved: string;
  whyThisIssueWasFlagged: string;
  waterPriorityScore: string;
  cropWaterSensitivity: string;
  growthStageImportance: string;
  overallPriority: string;
  waterShortageDesc: string;
  apiConnected: string;
  backendOffline: string;
  checkingApi: string;

  // Farmer Home
  myWaterSharing: string;
  myWaterSharingDesc: string;
  selectFarmer: string;
  viewingFor: string;
  noScenarioTitle: string;
  noScenarioDesc: string;
  startScenarioBtn: string;

  // 4 Large Cards
  waterGivenToMe: string;
  waterGivenDesc: string;
  waterNeeded: string;
  waterNeededDesc: string;
  waterAvailable: string;
  waterAvailableDesc: string;
  sharingResult: string;
  sharingResultDesc: string;

  // Result Summary Card
  yourResultTitle: string;
  requestedLabel: string;
  receivedLabel: string;
  satisfiedLabel: string;
  surplusNote: string;
  shortageNote: string;
  agreementReachedNote: string;
  agreementPendingNote: string;

  // Why did I get this amount?
  whyTitle: string;
  whySubtitle: string;

  // Reason Codes (Simple plain-language translations)
  reasonResourceShortageTitle: string;
  reasonResourceShortageDesc: string;
  reasonHighUrgencyTitle: string;
  reasonHighUrgencyDesc: string;
  reasonHighCropSensitivityTitle: string;
  reasonHighCropSensitivityDesc: string;
  reasonMinimumRequirementTitle: string;
  reasonMinimumRequirementDesc: string;
  reasonMaximumRequirementTitle: string;
  reasonMaximumRequirementDesc: string;
  reasonCanalCapacityTitle: string;
  reasonCanalCapacityDesc: string;
  reasonWindowConflictTitle: string;
  reasonWindowConflictDesc: string;
  reasonFairnessAdjustmentTitle: string;
  reasonFairnessAdjustmentDesc: string;
  reasonNegotiationConcessionTitle: string;
  reasonNegotiationConcessionDesc: string;
  reasonBatnaProtectionTitle: string;
  reasonBatnaProtectionDesc: string;
  reasonUnmetDemandTitle: string;
  reasonUnmetDemandDesc: string;
  reasonFullSatisfactionTitle: string;
  reasonFullSatisfactionDesc: string;
  reasonWaterSurplusTitle: string;
  reasonWaterSurplusDesc: string;

  // Simple Conflicts
  conflictSectionTitle: string;
  conflictSectionSubtitle: string;
  noConflictsFound: string;
  conflictWaterShortage: string;
  conflictWaterShortageDesc: string;
  conflictWindowOverlap: string;
  conflictWindowOverlapDesc: string;
  conflictCanalCapacity: string;
  conflictCanalCapacityDesc: string;
  conflictMinRequirement: string;
  conflictMinRequirementDesc: string;
  conflictHighCropStress: string;
  conflictHighCropStressDesc: string;
  conflictTimingDetected: string;
  conflictSingularDetected: string;
  conflictPluralDetected: string;
  whatHappened: string;
  whyItMatters: string;

  // How was water shared? (Simple Negotiation)
  howSharedTitle: string;
  howSharedSubtitle: string;
  step1: string;
  step1Desc: string;
  step2: string;
  step2Desc: string;
  step3: string;
  step3Desc: string;
  step4: string;
  step4Desc: string;
  step5: string;
  step5Desc: string;

  // Simple Fairness
  fairSharingTitle: string;
  fairSharingDesc: string;
  fairSharingNote: string;

  // Expandable Technical Details
  techDetailsTitle: string;
  techDetailsSubtitle: string;
  modelUsed: string;
  lpSolver: string;
  fairnessScore: string;
  rawCodes: string;

  // Farmer Scenario Configuration
  startWaterSharingTitle: string;
  startWaterSharingSubtitle: string;
  q1SituationTitle: string;
  q1OptEnoughTitle: string;
  q1OptEnoughDesc: string;
  q1OptSomeShortageTitle: string;
  q1OptSomeShortageDesc: string;
  q1OptSeriousShortageTitle: string;
  q1OptSeriousShortageDesc: string;
  q1OptCropsUrgentTitle: string;
  q1OptCropsUrgentDesc: string;
  q2FarmersTitle: string;
  q2FarmersLabel: string;
  q2FarmersHelper: string;
  q5WaterAvailableTitle: string;
  q5WaterAvailableHelper: string;
  q5UnknownCheckbox: string;
  farmerConfigUsageNote: string;
  findWaterPlanBtn: string;
  findWaterPlanBtnHelper: string;
  findingWaterPlanTitle: string;
  findingStage1: string;
  findingStage2: string;
  findingStage3: string;
  findingStage4: string;
  findingStage5: string;

  // Explainability Page
  explainPageTitleFarmer: string;
  explainPageSubtitleFarmer: string;
  explainResultCardTitle: string;
  explainWhySectionTitle: string;
  explainConflictSectionTitle: string;
  explainFairnessSectionTitle: string;
  explainFairnessText: string;
  explainNegotiationSectionTitle: string;
  explainNegotiationText1: string;
  explainNegotiationText2: string;
  explainNegotiationText3: string;
  explainExpertPageTitle: string;
  explainExpertPageSubtitle: string;
  shapUnavailableText: string;

  // Phase 14: Farmer Portal Page
  farmerPortalTitle: string;
  farmerPortalDesc: string;

  // Government portal, welcome & authentication
  welcomePortalTitle: string;
  welcomePortalSubtitle: string;
  welcomeRolePrompt: string;
  farmerCardTitle: string;
  farmerCardBadge: string;
  farmerCardDesc: string;
  farmerCardBtn: string;
  expertCardTitle: string;
  expertCardBadge: string;
  expertCardDesc: string;
  expertCardBtn: string;
  loginTitle: string;
  loginSubtitle: string;
  loginEmailLabel: string;
  loginPasswordLabel: string;
  loginSubmitBtn: string;
  loginBackBtn: string;
  activeModelLabel: string;
  governmentBadge: string;
  logoutBtn: string;
  farmerModeActive: string;
  expertModeActive: string;
}

export const TRANSLATIONS: Record<Language, Translations> = {
  en: {
    appTitle: 'AquaMediAI',
    appSubtitle: 'Water Sharing Assistant',
    farmerView: '👨‍🌾 Farmer View',
    expertView: '🔬 Expert View',
    waterConflictMonitor: 'Water Conflict Monitor',
    waterConflictsFound: 'Water Conflicts Found',
    mostUrgentIssue: 'Most Urgent Issue',
    waterShortage: 'Water Shortage',
    availableWaterVsFarmDemand: 'Available Water vs Farm Demand',
    overlappingIrrigationSchedules: 'Overlapping Irrigation Schedules',
    highWaterPriority: 'High Water Priority',
    farmsInvolved: 'Farms Involved',
    whyThisIssueWasFlagged: 'Why This Issue Was Flagged',
    waterPriorityScore: 'Water Priority Score',
    cropWaterSensitivity: 'Crop Water Sensitivity',
    growthStageImportance: 'Growth-Stage Importance',
    overallPriority: 'Overall Priority',
    waterShortageDesc: 'Total water available was lower than total farmer demand.',
    apiConnected: 'API Connected',
    backendOffline: 'Backend Offline',
    checkingApi: 'Checking API...',

    myWaterSharing: '💧 My Water Sharing',
    myWaterSharingDesc: 'Clear, simple view of your crop water allocation.',
    selectFarmer: 'Select Farmer',
    viewingFor: 'Viewing water details for',
    noScenarioTitle: 'No Water Plan Loaded',
    noScenarioDesc: 'Start an automated water sharing plan to see your allocation.',
    startScenarioBtn: 'Run Water Sharing Plan',

    waterGivenToMe: '💧 Water Given To Me',
    waterGivenDesc: 'This is the amount of water allocated to you.',
    waterNeeded: '🌱 Water Needed',
    waterNeededDesc: 'Estimated water needed for your crop.',
    waterAvailable: '💦 Water Available',
    waterAvailableDesc: 'Total canal water available for all farmers.',
    sharingResult: '🤝 Sharing Result',
    sharingResultDesc: 'The water-sharing plan was accepted.',

    yourResultTitle: '🤝 Your Water Sharing Result',
    requestedLabel: 'You requested',
    receivedLabel: 'You received',
    satisfiedLabel: 'Need satisfied',
    surplusNote: 'Sufficient water was available to satisfy everyone’s needs.',
    shortageNote: 'Some water was unavailable because total demand was higher than canal supply.',
    agreementReachedNote: 'Agreement reached: all farmers accepted the sharing plan.',
    agreementPendingNote: 'Best feasible allocation determined to balance crop needs.',

    whyTitle: 'Why did I get this amount?',
    whySubtitle: 'Clear reasons explaining your water allocation:',

    reasonResourceShortageTitle: '💧 Water was limited',
    reasonResourceShortageDesc: 'Not enough water was available for everyone to receive their full requirement.',
    reasonHighUrgencyTitle: '🚨 Urgent crop needs',
    reasonHighUrgencyDesc: 'Some crop water requirements were more urgent.',
    reasonHighCropSensitivityTitle: '🌱 Crop sensitivity',
    reasonHighCropSensitivityDesc: 'The system considered how strongly the crop could be affected by low water.',
    reasonMinimumRequirementTitle: '💧 Minimum water need considered',
    reasonMinimumRequirementDesc: 'The system considered the minimum water requirement while allocating the available water.',
    reasonMaximumRequirementTitle: '📏 Water limit considered',
    reasonMaximumRequirementDesc: 'The allocation stayed within the allowed water requirement.',
    reasonCanalCapacityTitle: '🚰 Canal capacity considered',
    reasonCanalCapacityDesc: 'The canal could not provide unlimited water at the same time.',
    reasonWindowConflictTitle: '🕐 Timing conflicts considered',
    reasonWindowConflictDesc: 'Some farmers needed water during overlapping irrigation periods.',
    reasonFairnessAdjustmentTitle: '⚖️ Fair sharing considered',
    reasonFairnessAdjustmentDesc: 'The available water was distributed while considering fairness.',
    reasonNegotiationConcessionTitle: '🤝 Requests were adjusted',
    reasonNegotiationConcessionDesc: 'The mediation process considered adjusted water requests.',
    reasonBatnaProtectionTitle: '🛡️ Minimum acceptable outcome considered',
    reasonBatnaProtectionDesc: 'The system considered the minimum acceptable outcome for the farmer.',
    reasonUnmetDemandTitle: '💧 Some water need remained',
    reasonUnmetDemandDesc: 'Available water was lower than the total amount requested.',
    reasonFullSatisfactionTitle: '✅ Full water need met',
    reasonFullSatisfactionDesc: 'The requested water amount was satisfied.',
    reasonWaterSurplusTitle: '🌊 Ample water supply',
    reasonWaterSurplusDesc: 'Canal flow was high enough to cover all irrigation demands.',

    conflictSectionTitle: '⚠️ Irrigation Issues Found',
    conflictSectionSubtitle: 'Issues identified before sharing was solved:',
    noConflictsFound: 'No issues found! Water supply is sufficient for all farmers.',
    conflictWaterShortage: '💧 Water shortage',
    conflictWaterShortageDesc: 'Total water available was lower than total farmer demand.',
    conflictWindowOverlap: '🕐 Timing conflicts',
    conflictWindowOverlapDesc: 'Some farmers needed water during overlapping irrigation periods.',
    conflictCanalCapacity: '🚰 Canal capacity issue',
    conflictCanalCapacityDesc: 'The canal could not provide unlimited water at the same time.',
    conflictMinRequirement: '💧 Minimum water requirement conflict',
    conflictMinRequirementDesc: 'The system considered the minimum water requirement while allocating the available water.',
    conflictHighCropStress: '🌱 High crop water stress',
    conflictHighCropStressDesc: 'Some crops had higher water stress.',
    conflictTimingDetected: 'timing conflicts were detected',
    conflictSingularDetected: 'conflict was',
    conflictPluralDetected: 'conflicts were',
    whatHappened: 'What happened?',
    whyItMatters: 'Why does it matter?',

    howSharedTitle: '🤝 How was the water shared?',
    howSharedSubtitle: 'The 5-step automated water mediation process:',
    step1: '1. Crop Needs Checked',
    step1Desc: 'Each farmer’s crop type and soil moisture was analyzed.',
    step2: '2. Canal Water Checked',
    step2Desc: 'Available supply from the canal was verified.',
    step3: '3. Conflicts Identified',
    step3Desc: 'Shortages and overlapping timings were flagged.',
    step4: '4. Sharing Adjusted',
    step4Desc: 'Allocations were adjusted fairly to protect survival minimums.',
    step5: '5. Final Agreement Reached',
    step5Desc: 'All farmers accepted the balanced water-sharing plan.',

    fairSharingTitle: '⚖️ Fair Sharing',
    fairSharingDesc: 'The available water was distributed while considering fairness between farmers.',
    fairSharingNote: 'Balanced sharing ensures no farmer is left without survival water.',

    techDetailsTitle: 'Technical Details (Optional)',
    techDetailsSubtitle: 'Click to view advanced data for evaluators and researchers',
    modelUsed: 'AI Prediction Model',
    lpSolver: 'Optimization Solver',
    fairnessScore: 'Fairness Measurement',
    rawCodes: 'Raw Reason Codes',

    // Farmer Scenario Configuration
    startWaterSharingTitle: '💧 Start Water Sharing',
    startWaterSharingSubtitle: 'Tell us about the water situation and we will find a suitable sharing plan.',
    q1SituationTitle: '💧 How is the water situation today?',
    q1OptEnoughTitle: '💧 Enough Water',
    q1OptEnoughDesc: 'There is enough water for the farmers.',
    q1OptSomeShortageTitle: '💧 Some Shortage',
    q1OptSomeShortageDesc: 'There is less water than farmers need.',
    q1OptSeriousShortageTitle: '🚨 Serious Shortage',
    q1OptSeriousShortageDesc: 'There is much less water than farmers need.',
    q1OptCropsUrgentTitle: '🌱 Crops Need Water Urgently',
    q1OptCropsUrgentDesc: 'Crops are under high water stress and need water quickly.',
    q2FarmersTitle: '👨‍🌾 How many farmers are sharing the water?',
    q2FarmersLabel: 'Farmers sharing this water',
    q2FarmersHelper: 'Tell us how many farmers are sharing the water.',
    q5WaterAvailableTitle: '💦 How much water is available?',
    q5WaterAvailableHelper: 'Optional — leave blank to use the scenario’s normal water supply.',
    q5UnknownCheckbox: 'I don’t know the exact amount',
    farmerConfigUsageNote: 'Your information is used to calculate the water-sharing plan.',
    findWaterPlanBtn: '💧 Find Water Sharing Plan',
    findWaterPlanBtnHelper: 'We will check water needs, conflicts and fair sharing.',
    findingWaterPlanTitle: '💧 Finding a Water Sharing Plan',
    findingStage1: '🌱 Checking crop water needs',
    findingStage2: '💧 Checking available water',
    findingStage3: '⚠️ Finding water conflicts',
    findingStage4: '⚖️ Sharing available water',
    findingStage5: '🤝 Checking the final agreement',

    // Explainability Page
    explainPageTitleFarmer: '💧 Why Did I Get This Much Water?',
    explainPageSubtitleFarmer: 'AquaMediAI looked at the water available, crop needs and other farmers’ needs before preparing the sharing plan.',
    explainResultCardTitle: '💧 Your Water Result',
    explainWhySectionTitle: '💡 Why did I get this amount?',
    explainConflictSectionTitle: '⚠️ What affected the water sharing?',
    explainFairnessSectionTitle: '⚖️ Was the sharing fair?',
    explainFairnessText: 'Fairness was considered while distributing the available water.',
    explainNegotiationSectionTitle: '🤝 How was the plan agreed?',
    explainNegotiationText1: 'The system’s farmer agents evaluated the proposed water allocation.',
    explainNegotiationText2: 'If the proposed allocation did not satisfy the required conditions, the mediation process evaluated adjustments.',
    explainNegotiationText3: 'Every revised allocation was checked against the water constraints.',
    explainExpertPageTitle: '🔬 Decision Explanation',
    explainExpertPageSubtitle: 'Trace how AquaMediAI moved from predicted water demand to the final sharing agreement.',
    shapUnavailableText: 'Detailed feature attribution was not available for this prediction.',
    farmerPortalTitle: 'Check My Farm Water Need',
    farmerPortalDesc: 'Enter your farm details below to get an AI-calculated water demand estimate for today.',
    welcomePortalTitle: 'Agricultural Decision Support System',
    welcomePortalSubtitle: 'Government-Grade Water Dispute Mediation & Crop Health Intelligence',
    welcomeRolePrompt: 'Select your portal access level to continue:',
    farmerCardTitle: 'Farmer Access',
    farmerCardBadge: 'Frictionless Access • No Credentials Required',
    farmerCardDesc: 'Immediate access to daily crop water demand predictions, farm health diagnostics, irrigation schedules, and weather advisories.',
    farmerCardBtn: 'Continue as Farmer',
    expertCardTitle: 'Agricultural Expert Access',
    expertCardBadge: 'Official Government Authentication Required',
    expertCardDesc: 'Dedicated portal for agricultural extension officers, agronomists, and dispute mediators. Access multi-agent mediation, LP allocations, and model diagnostics.',
    expertCardBtn: 'Sign In as Agricultural Expert',
    loginTitle: 'Agricultural Expert Sign-In',
    loginSubtitle: 'Enter your official credentials to access the mediation system',
    loginEmailLabel: 'Username or Official Email',
    loginPasswordLabel: 'Password',
    loginSubmitBtn: 'Authenticate & Enter',
    loginBackBtn: 'Back to Role Selection',
    activeModelLabel: 'Active Prediction Model: XGBoost (Verified Production)',
    governmentBadge: 'Department of Agriculture & Water Resources • Official Platform',
    logoutBtn: 'Sign Out',
    farmerModeActive: 'Farmer Guest Mode',
    expertModeActive: 'Agricultural Extension Officer',
  },

  hi: {
    appTitle: 'AquaMediAI',
    appSubtitle: 'जल वितरण सहायक',
    farmerView: '👨‍🌾 किसान दृश्य',
    expertView: '🔬 विशेषज्ञ दृश्य',

    waterConflictMonitor: 'पानी विवाद मॉनिटर',
    waterConflictsFound: 'पानी विवाद मिले',
    mostUrgentIssue: 'सबसे तात्कालिक समस्या',
    waterShortage: 'पानी की कमी',
    availableWaterVsFarmDemand: 'उपलब्ध पानी बनाम खेत की मांग',
    overlappingIrrigationSchedules: 'एक ही समय की सिंचाई विंडो',
    highWaterPriority: 'उच्च पानी प्राथमिकता',
    farmsInvolved: 'शामिल खेत',
    whyThisIssueWasFlagged: 'यह मुद्दा क्यों चिन्हित किया गया',
    waterPriorityScore: 'पानी प्राथमिकता स्कोर',
    cropWaterSensitivity: 'फसल पानी संवेदनशीलता',
    growthStageImportance: 'विकास-चरण महत्व',
    overallPriority: 'कुल प्राथमिकता',
    waterShortageDesc: 'कुल उपलब्ध पानी किसानों की कुल मांग से कम था।',
    apiConnected: 'सिस्टम जुड़ा हुआ है',
    backendOffline: 'सिस्टम ऑफ़लाइन है',
    checkingApi: 'जाँच जारी है...',


    myWaterSharing: '💧 मेरा पानी वितरण',
    myWaterSharingDesc: 'आपकी फसल के पानी आवंटन की सरल जानकारी।',
    selectFarmer: 'किसान चुनें',
    viewingFor: 'पानी का विवरण किसान के लिए:',
    noScenarioTitle: 'कोई जल योजना लोड नहीं है',
    noScenarioDesc: 'अपना पानी आवंटन देखने के लिए जल वितरण योजना शुरू करें।',
    startScenarioBtn: 'जल वितरण योजना चलाएं',

    waterGivenToMe: '💧 मुझे मिला हुआ पानी',
    waterGivenDesc: 'यह आपको आवंटित किया गया पानी है।',
    waterNeeded: '🌱 पानी की आवश्यकता',
    waterNeededDesc: 'आपकी फसल के लिए अनुमानित आवश्यक पानी।',
    waterAvailable: '💦 कुल उपलब्ध पानी',
    waterAvailableDesc: 'सभी किसानों के लिए नहर में उपलब्ध कुल पानी।',
    sharingResult: '🤝 वितरण परिणाम',
    sharingResultDesc: 'पानी बांटने की योजना स्वीकार कर ली गई।',

    yourResultTitle: '🤝 आपका जल वितरण परिणाम',
    requestedLabel: 'आपने मांगा था',
    receivedLabel: 'आपको मिला',
    satisfiedLabel: 'संतुष्टि स्तर',
    surplusNote: 'पर्याप्त पानी उपलब्ध था, सभी किसानों की ज़रूरत पूरी हुई।',
    shortageNote: 'कुल मांग नहर के पानी से अधिक होने के कारण कुछ कटौती की गई।',
    agreementReachedNote: 'सहमति बनी: सभी किसानों ने जल वितरण योजना स्वीकार की।',
    agreementPendingNote: 'फसलों की सुरक्षा के लिए सबसे उचित वितरण तय किया गया।',

    whyTitle: 'मुझे इतना पानी क्यों मिला?',
    whySubtitle: 'आपके आवंटन के प्रमुख कारण:',

    reasonResourceShortageTitle: '💧 पानी सीमित था',
    reasonResourceShortageDesc: 'सभी को पूरा पानी देने के लिए नहर में पर्याप्त पानी नहीं था।',
    reasonHighUrgencyTitle: '🚨 पानी की तुरंत आवश्यकता थी',
    reasonHighUrgencyDesc: 'फसल की तात्कालिक पानी की जरूरत को ध्यान में रखा गया।',
    reasonHighCropSensitivityTitle: '🌱 फसल कम पानी के प्रति संवेदनशील है',
    reasonHighCropSensitivityDesc: 'कम पानी से फसल पर पड़ने वाले प्रभाव का ध्यान रखा गया।',
    reasonMinimumRequirementTitle: '💧 न्यूनतम आवश्यकता पर विचार किया गया',
    reasonMinimumRequirementDesc: 'उपलब्ध पानी का आवंटन करते समय न्यूनतम पानी की आवश्यकता को ध्यान में रखा गया।',
    reasonMaximumRequirementTitle: '📏 अधिकतम सीमा का ध्यान रखा गया',
    reasonMaximumRequirementDesc: 'आवंटन अधिकतम सीमा के भीतर रहा।',
    reasonCanalCapacityTitle: '🚰 नहर की क्षमता का ध्यान रखा गया',
    reasonCanalCapacityDesc: 'नहर से बहने वाले पानी की अधिकतम क्षमता को ध्यान में रखा गया।',
    reasonWindowConflictTitle: '🕐 पानी का समय एक ही था',
    reasonWindowConflictDesc: 'कुछ किसानों को एक ही समय पर पानी चाहिए था।',
    reasonFairnessAdjustmentTitle: '⚖️ निष्पक्ष वितरण का ध्यान रखा गया',
    reasonFairnessAdjustmentDesc: 'उपलब्ध पानी को किसानों के बीच निष्पक्ष रूप से बांटा गया।',
    reasonNegotiationConcessionTitle: '🤝 मांग में सहयोगपूर्वक समायोजन',
    reasonNegotiationConcessionDesc: 'मध्यस्थता के दौरान किसानों ने सहयोग से मांग में बदलाव किया।',
    reasonBatnaProtectionTitle: '🛡️ न्यूनतम स्वीकार्य सीमा सुरक्षित',
    reasonBatnaProtectionDesc: 'सुनिश्चित किया गया कि किसान को नुकसान न हो।',
    reasonUnmetDemandTitle: '💧 कुछ मांग पूरी नहीं हो सकी',
    reasonUnmetDemandDesc: 'कुल मांग की तुलना में पानी कम उपलब्ध था।',
    reasonFullSatisfactionTitle: '✅ पूरी मांग संतुष्ट हुई',
    reasonFullSatisfactionDesc: 'मांगा गया 100% पानी प्रदान किया गया।',
    reasonWaterSurplusTitle: '🌊 प्रचुर पानी उपलब्ध था',
    reasonWaterSurplusDesc: 'सभी किसानों की सिंचाई के लिए नहर में पर्याप्त पानी था।',

    conflictSectionTitle: '⚠️ सिंचाई से जुड़ी समस्याएं',
    conflictSectionSubtitle: 'वितरण से पहले पहचानी गई समस्याएं:',
    noConflictsFound: 'कोई समस्या नहीं! सभी किसानों के लिए पर्याप्त पानी है।',
    conflictWaterShortage: '💧 पानी की कमी',
    conflictWaterShortageDesc: 'उपलब्ध पानी किसानों की कुल मांग से कम था।',
    conflictWindowOverlap: '🕐 समय का टकराव',
    conflictWindowOverlapDesc: 'कुछ किसानों को एक ही समय पर सिंचाई की जरूरत थी।',
    conflictCanalCapacity: '🚰 नहर क्षमता की समस्या',
    conflictCanalCapacityDesc: 'नहर एक साथ असीमित पानी नहीं दे सकती।',
    conflictMinRequirement: '💧 न्यूनतम आवश्यकता का टकराव',
    conflictMinRequirementDesc: 'पानी बांटते समय न्यूनतम पानी की जरूरत को ध्यान में रखा गया।',
    conflictHighCropStress: '🌱 फसल में अधिक तनाव',
    conflictHighCropStressDesc: 'कुछ फसलों पर पानी की कमी का ज्यादा असर था।',
    conflictTimingDetected: 'समय के टकराव मिले',
    conflictSingularDetected: 'समस्या मिली',
    conflictPluralDetected: 'समस्याएं मिलीं',
    whatHappened: 'क्या हुआ?',
    whyItMatters: 'यह क्यों महत्वपूर्ण है?',

    howSharedTitle: '🤝 पानी कैसे बांटा गया?',
    howSharedSubtitle: '5 चरणों में स्वचालित जल मध्यस्थता प्रक्रिया:',
    step1: '1. फसल की आवश्यकता जांची गई',
    step1Desc: 'फसल के प्रकार और मिट्टी की नमी का आकलन किया गया।',
    step2: '2. उपलब्ध नहर का पानी जांचा गया',
    step2Desc: 'नहर में उपलब्ध कुल पानी की मात्रा सत्यापित की गई।',
    step3: '3. टकरावों की पहचान की गई',
    step3Desc: 'कमी और एक ही समय की मांगों को पहचाना गया।',
    step4: '4. वितरण में संतुलन बनाया गया',
    step4Desc: 'सभी की न्यूनतम जरूरतों की रक्षा करते हुए पानी बांटा गया।',
    step5: '5. अंतिम सहमति बनी',
    step5Desc: 'संतुलित योजना पर सभी ने सहमति जताई।',

    fairSharingTitle: '⚖️ निष्पक्ष वितरण',
    fairSharingDesc: 'उपलब्ध पानी को किसानों के बीच निष्पक्षता को ध्यान में रखकर बांटा गया।',
    fairSharingNote: 'संतुलित वितरण से किसी भी किसान की फसल बर्बाद नहीं होती।',

    techDetailsTitle: 'तकनीकी विवरण (ऐच्छिक)',
    techDetailsSubtitle: 'मूल्यांकनकर्ताओं और शोधकर्ताओं के लिए उन्नत विवरण देखने के लिए क्लिक करें',
    modelUsed: 'एआई पूर्वानुमान मॉडल',
    lpSolver: 'इष्टतमीकरण सॉल्वर',
    fairnessScore: 'निष्पक्षता माप',
    rawCodes: 'कारण कोड',

    // Farmer Scenario Configuration
    startWaterSharingTitle: '💧 जल वितरण शुरू करें',
    startWaterSharingSubtitle: 'पानी की स्थिति के बारे में बताएं, हम उचित वितरण योजना तैयार करेंगे।',
    q1SituationTitle: '💧 आज पानी की स्थिति कैसी है?',
    q1OptEnoughTitle: '💧 पर्याप्त पानी',
    q1OptEnoughDesc: 'किसानों के लिए पर्याप्त पानी उपलब्ध है।',
    q1OptSomeShortageTitle: '💧 कुछ कमी',
    q1OptSomeShortageDesc: 'किसानों की जरूरत से कम पानी उपलब्ध है।',
    q1OptSeriousShortageTitle: '🚨 गंभीर कमी',
    q1OptSeriousShortageDesc: 'किसानों की जरूरत से बहुत कम पानी उपलब्ध है।',
    q1OptCropsUrgentTitle: '🌱 फसलों को तुरंत पानी चाहिए',
    q1OptCropsUrgentDesc: 'फसलें गंभीर तनाव में हैं और उन्हें तुरंत पानी की आवश्यकता है।',
    q2FarmersTitle: '👨‍🌾 पानी साझा करने वाले कितने किसान हैं?',
    q2FarmersLabel: 'पानी साझा करने वाले किसान',
    q2FarmersHelper: 'बताएं कि कितने किसान इस पानी का उपयोग कर रहे हैं।',
    q5WaterAvailableTitle: '💦 कितना पानी उपलब्ध है?',
    q5WaterAvailableHelper: 'ऐच्छिक — सामान्य आपूर्ति का उपयोग करने के लिए इसे खाली छोड़ें।',
    q5UnknownCheckbox: 'मुझे सही मात्रा पता नहीं है',
    farmerConfigUsageNote: 'आपकी जानकारी का उपयोग जल वितरण योजना की गणना के लिए किया जाता है।',
    findWaterPlanBtn: '💧 जल वितरण योजना खोजें',
    findWaterPlanBtnHelper: 'हम पानी की ज़रूरत, विवाद और निष्पक्ष वितरण की जाँच करेंगे।',
    findingWaterPlanTitle: '💧 जल वितरण योजना खोजी जा रही है',
    findingStage1: '🌱 फसलों की पानी की ज़रूरत जांची जा रही है',
    findingStage2: '💧 उपलब्ध पानी की जाँच की जा रही है',
    findingStage3: '⚠️ पानी के टकरावों की पहचान की जा रही है',
    findingStage4: '⚖️ उपलब्ध पानी का निष्पक्ष बँटवारा किया जा रहा है',
    findingStage5: '🤝 अंतिम सहमति की पुष्टि की जा रही है',

    // Explainability Page
    explainPageTitleFarmer: '💧 मुझे इतना पानी क्यों मिला?',
    explainPageSubtitleFarmer: 'AquaMediAI ने वितरण योजना तैयार करने से पहले उपलब्ध पानी, फसल की ज़रूरतों और अन्य किसानों की ज़रूरतों का आकलन किया।',
    explainResultCardTitle: '💧 आपका जल वितरण परिणाम',
    explainWhySectionTitle: '💡 मुझे इतना पानी क्यों मिला?',
    explainConflictSectionTitle: '⚠️ पानी वितरण को किन बातों ने प्रभावित किया?',
    explainFairnessSectionTitle: '⚖️ क्या पानी का वितरण निष्पक्ष था?',
    explainFairnessText: 'उपलब्ध पानी का वितरण करते समय निष्पक्षता का ध्यान रखा गया था।',
    explainNegotiationSectionTitle: '🤝 योजना पर सहमति कैसे बनी?',
    explainNegotiationText1: 'प्रणाली के किसान एजेंटों ने प्रस्तावित पानी आवंटन का मूल्यांकन किया।',
    explainNegotiationText2: 'यदि प्रस्तावित आवंटन आवश्यक शर्तों को पूरा नहीं करता था, तो मध्यस्थता प्रक्रिया ने समायोजन का मूल्यांकन किया।',
    explainNegotiationText3: 'प्रत्येक संशोधित आवंटन की पानी की सीमाओं के विरुद्ध जाँच की गई।',
    explainExpertPageTitle: '🔬 निर्णय स्पष्टीकरण',
    explainExpertPageSubtitle: 'देखें कि AquaMediAI अनुमानित पानी की माँग से अंतिम सहमति तक कैसे पहुँचा।',
    shapUnavailableText: 'इस पूर्वानुमान के लिए विस्तृत विशेषता योगदान उपलब्ध नहीं था।',
    farmerPortalTitle: 'मेरे खेत की पानी की ज़रूरत जांचें',
    farmerPortalDesc: 'आज के लिए AI-आधारित पानी की माँग का अनुमान पाने के लिए नीचे अपने खेत का विवरण दर्ज करें।',
    welcomePortalTitle: 'कृषि निर्णय सहायता प्रणाली',
    welcomePortalSubtitle: 'सरकारी स्तर की जल विवाद मध्यस्थता और फसल स्वास्थ्य बुद्धिमत्ता',
    welcomeRolePrompt: 'जारी रखने के लिए अपना पोर्टल स्तर चुनें:',
    farmerCardTitle: 'किसान प्रवेश',
    farmerCardBadge: 'तत्काल प्रवेश • किसी पासवर्ड की आवश्यकता नहीं',
    farmerCardDesc: 'दैनिक फसल जल मांग अनुमान, सिंचाई सलाह और मौसम की जानकारी तुरंत देखें।',
    farmerCardBtn: 'किसान के रूप में आगे बढ़ें',
    expertCardTitle: 'कृषि विशेषज्ञ प्रवेश',
    expertCardBadge: 'आधिकारिक प्रमाणीकरण आवश्यक',
    expertCardDesc: 'कृषि विस्तार अधिकारियों और मध्यस्थों के लिए। मल्टी-एजेंट मध्यस्थता और मॉडल विश्लेषण देखें।',
    expertCardBtn: 'कृषि विशेषज्ञ के रूप में लॉगिन करें',
    loginTitle: 'कृषि विशेषज्ञ लॉगिन',
    loginSubtitle: 'मध्यस्थता प्रणाली में प्रवेश करने के लिए अपने क्रेडेंशियल दर्ज करें',
    loginEmailLabel: 'उपयोगकर्ता नाम या आधिकारिक ईमेल',
    loginPasswordLabel: 'पासवर्ड',
    loginSubmitBtn: 'प्रमाणित करें और प्रवेश करें',
    loginBackBtn: 'वापस जाएं',
    activeModelLabel: 'सक्रिय भविष्यवाणी मॉडल: XGBoost (सत्यापित उत्पादन)',
    governmentBadge: 'कृषि एवं जल संसाधन विभाग • आधिकारिक मंच',
    logoutBtn: 'लॉगआउट',
    farmerModeActive: 'किसान गेस्ट मोड',
    expertModeActive: 'कृषि विस्तार अधिकारी',
  },

  gu: {
    appTitle: 'AquaMediAI',
    appSubtitle: 'પાણી વહેંચણી સહાયક',
    farmerView: '👨‍🌾 ખેડૂત દૃશ્ય',
    expertView: '🔬 નિષ્ણાત દૃશ્ય',

    waterConflictMonitor: 'पाणी विरोध मॉन्टर',
    waterConflictsFound: 'पाणी विरोध पोटेन',
    mostUrgentIssue: 'श्रेष्ठ परम समस्या',
    waterShortage: 'पाणी कमी',
    availableWaterVsFarmDemand: 'उपलब्ध पानी बनता खेताची मांड',
    overlappingIrrigationSchedules: 'एकजेव्हा सिंचाई नलकावळे',
    highWaterPriority: 'उच्च पानी प्राथमिकता',
    farmsInvolved: 'शामिल खेट',
    whyThisIssueWasFlagged: 'आणि ही मुद्दा कँ सेंकोळी करायला मिळाली',
    waterPriorityScore: 'पाणी प्राथमिकता स्कॉड',
    cropWaterSensitivity: 'फसल पाणी संवेदनशीलता',
    growthStageImportance: 'विकास-च बाबत महत्त्व',
    overallPriority: 'સર્વ પ્રાથમિકતા',
    waterShortageDesc: 'કુલ ઉપલબ્ધ પાણી ખેડૂતોની કુલ માંગ કરતાં ઓછું હતું.',
    apiConnected: 'સિસ્ટમ જોડાયેલ છે',
    backendOffline: 'સિસ્ટમ ઑફલાઇન છે',
    checkingApi: 'ચકાસણી ચાલી રહી છે...',
    myWaterSharing: '💧 મારી પાણીની વહેંચણી',
    myWaterSharingDesc: 'તમારા પાક માટે ફાળવેલ પાણીની સરળ માહિતી.',
    selectFarmer: 'ખેડૂત પસંદ કરો',
    viewingFor: 'પાણીની વિગતો ખેડૂત માટે:',
    noScenarioTitle: 'કોઈ યોજના લોડ નથી',
    noScenarioDesc: 'તમારી પાણીની ફાળવણી જોવા માટે વહેંચણી યોજના શરૂ કરો.',
    startScenarioBtn: 'પાણી વહેંચણી યોજના ચલાવો',

    waterGivenToMe: '💧 મને મળેલું પાણી',
    waterGivenDesc: 'આ તમને ફાળવવામાં આવેલું પાણી છે.',
    waterNeeded: '🌱 પાણીની જરૂરિયાત',
    waterNeededDesc: 'તમારા પાક માટે અંદાજિત જરૂરી પાણી.',
    waterAvailable: '💦 કુલ ઉપલબ્ધ પાણી',
    waterAvailableDesc: 'બધા ખેડૂતો માટે નહેરમાં કુલ ઉપલબ્ધ પાણી.',
    sharingResult: '🤝 વહેંચણીનું પરિણામ',
    sharingResultDesc: 'પાણી વહેંચણીની યોજના સ્વીકારવામાં આવી.',

    yourResultTitle: '🤝 તમારું પાણી વહેંચણી પરિણામ',
    requestedLabel: 'તમે માંગેલું',
    receivedLabel: 'તમને મળેલું',
    satisfiedLabel: 'સંતોષ દર',
    surplusNote: 'પર્યાપ્ત પાણી ઉપલબ્ધ હતું, બધા ખેડૂતોની જરૂરિયાત પૂરી થઈ.',
    shortageNote: 'નહેરમાં પાણી ઓછું હોવાથી થોડી કાપ મૂકવામાં આવી.',
    agreementReachedNote: 'સહમતિ સધાઈ: બધા ખેડૂતોએ પાણી વહેંચણી સ્વીકારી.',
    agreementPendingNote: 'પાકના રક્ષણ માટે શ્રેષ્ઠ વહેંચણી નક્કી કરવામાં આવી.',

    whyTitle: 'મને આટલું પાણી કેમ મળ્યું?',
    whySubtitle: 'તમારી ફાળવણીના મુખ્ય કારણો:',

    reasonResourceShortageTitle: '💧 પાણી મર્યાદિત હતું',
    reasonResourceShortageDesc: 'બધાને પૂરતું પાણી આપવા માટે નહેરમાં ઓછું પાણી હતું.',
    reasonHighUrgencyTitle: '🚨 પાણીની તાત્કાલિક જરૂર હતી',
    reasonHighUrgencyDesc: 'પાકની તાકીદની પાણીની જરૂરિયાત ધ્યાનમાં લેવામાં આવી.',
    reasonHighCropSensitivityTitle: '🌱 પાક પાણીની અછત પ્રત્યે સંવેદનશીલ છે',
    reasonHighCropSensitivityDesc: 'ઓછા પાણીથી પાક પર થતી અસર ધ્યાનમાં લેવાઈ.',
    reasonMinimumRequirementTitle: '💧 લઘુત્તમ જરૂરિયાત ધ્યાનમાં લેવાઈ',
    reasonMinimumRequirementDesc: 'ઉપલબ્ધ પાણીની ફાળવણી કરતી વખતે લઘુત્તમ પાણીની જરૂરિયાત ધ્યાનમાં લેવામાં આવી હતી.',
    reasonMaximumRequirementTitle: '📏 મહત્તમ મર્યાદા જળવાઈ',
    reasonMaximumRequirementDesc: 'ફાળવણી મંજૂર મહત્તમ મર્યાદામાં રહી.',
    reasonCanalCapacityTitle: '🚰 નહેરની ક્ષમતા ધ્યાનમાં લેવાઈ',
    reasonCanalCapacityDesc: 'નહેરમાંથી વહી શકતા પાણીની મર્યાદા ધ્યાનમાં લેવાઈ.',
    reasonWindowConflictTitle: '🕐 પાણીનો સમય એક જ હતો',
    reasonWindowConflictDesc: 'કેટલાક ખેડૂતોને એક જ સમયે પાણીની જરૂર હતી.',
    reasonFairnessAdjustmentTitle: '⚖️ ન્યાયી વહેંચણી ધ્યાનમાં લેવાઈ',
    reasonFairnessAdjustmentDesc: 'ઉપલબ્ધ પાણી ખેડૂતો વચ્ચે ન્યાયી રીતે વહેંચવામાં આવ્યું.',
    reasonNegotiationConcessionTitle: '🤝 માંગમાં સહકારી સુધારો',
    reasonNegotiationConcessionDesc: 'મધ્યસ્થી દરમિયાન ખેડૂતોએ સહકારથી માંગમાં સુધારો કર્યો.',
    reasonBatnaProtectionTitle: '🛡️ લઘુત્તમ સ્વીકાર્ય મર્યાદા સુરક્ષિત',
    reasonBatnaProtectionDesc: 'ખેડૂતને નુકસાન ન થાય તેની ખાતરી કરવામાં આવી.',
    reasonUnmetDemandTitle: '💧 કેટલીક માંગ પૂરી ન થઈ શકી',
    reasonUnmetDemandDesc: 'કુલ માંગ કરતાં ઉપલબ્ધ પાણી ઓછું હતું.',
    reasonFullSatisfactionTitle: '✅ પૂરી માંગ સંતોષાઈ',
    reasonFullSatisfactionDesc: 'માંગેલું ૧૦૦% પાણી ફાળવવામાં આવ્યું.',
    reasonWaterSurplusTitle: '🌊 વિપુલ પાણી ઉપલબ્ધ હતું',
    reasonWaterSurplusDesc: 'બધા ખેડૂતોની સિંચાઈ માટે નહેરમાં પૂરતું પાણી હતું.',

    conflictSectionTitle: '⚠️ સિંચાઈની સમસ્યાઓ',
    conflictSectionSubtitle: 'વહેંચણી પહેલાં ઓળખાયેલી સમસ્યાઓ:',
    noConflictsFound: 'કોઈ સમસ્યા નથી! બધા ખેડૂતો માટે પૂરતું પાણી છે.',
    conflictWaterShortage: '💧 પાણીની અછત',
    conflictWaterShortageDesc: 'ઉપલબ્ધ પાણી ખેડૂતોની કુલ માંગ કરતાં ઓછું હતું.',
    conflictWindowOverlap: '🕐 સમયનો સંઘર્ષ',
    conflictWindowOverlapDesc: 'કેટલાક ખેડૂતોને એક જ સમયે સિંચાઈની જરૂર હતી.',
    conflictCanalCapacity: '🚰 નહેર ક્ષમતાની સમસ્યા',
    conflictCanalCapacityDesc: 'નહેર એક સાથે અમર્યાદ પાણી આપી શકતી નથી.',
    conflictMinRequirement: '💧 લઘુત્તમ જરૂરિયાતનો સંઘર્ષ',
    conflictMinRequirementDesc: 'પાણી વહેંચતી વખતે લઘુત્તમ પાણીની જરૂરિયાત ધ્યાનમાં લેવામાં આવી.',
    conflictHighCropStress: '🌱 પાકમાં વધુ તણાવ',
    conflictHighCropStressDesc: 'કેટલાક પાક પર પાણીની અછતનો વધુ પ્રભાવ હતો.',
    conflictTimingDetected: 'સમયના સંઘર્ષો મળ્યા',
    conflictSingularDetected: 'સમસ્યા મળી',
    conflictPluralDetected: 'સમસ્યાઓ મળી',
    whatHappened: 'શું થયું?',
    whyItMatters: 'આ શા માટે મહત્વનું છે?',

    howSharedTitle: '🤝 પાણી કેવી રીતે વહેંચાયું?',
    howSharedSubtitle: '૫ પગલાંમાં સ્વચાલિત જળ મધ્યસ્થી પ્રક્રિયા:',
    step1: '૧. પાકની જરૂરિયાત તપાસી',
    step1Desc: 'પાકનો પ્રકાર અને જમીનના ભેજનું મૂલ્યાંકન થયું.',
    step2: '૨. નહેરનું પાણી તપાસ્યું',
    step2Desc: 'નહેરમાં ઉપલબ્ધ પાણીનો જથ્થો ચકાસવામાં આવ્યો.',
    step3: '૩. સમસ્યાઓની ઓળખ થઈ',
    step3Desc: 'અછત અને એક જ સમયની માંગણીઓ નોંધાઈ.',
    step4: '૪. વહેંચણીમાં સંતુલન કર્યું',
    step4Desc: 'બધાની ન્યૂનતમ જરૂરિયાતો સાચવીને પાણી વહેંચાયું.',
    step5: '૫. આખરી સહમતિ સધાઈ',
    step5Desc: 'સંતુલિત યોજના બધાએ સ્વીકારી લીધી.',

    fairSharingTitle: '⚖️ ન્યાયી વહેંચણી',
    fairSharingDesc: 'ઉપલબ્ધ પાણી ખેડૂતો વચ્ચે ન્યાયી ધોરણે વહેંચવામાં આવ્યું.',
    fairSharingNote: 'સંતુલિત વહેંચણીથી કોઈ ખેડૂતનો પાક બગડતો નથી.',

    techDetailsTitle: 'તકનીકી વિગતો (વૈકલ્પિક)',
    techDetailsSubtitle: 'મૂલ્યાંકનકારો અને સંશોધકો માટે વિગતવાર માહિતી જોવા ક્લિક કરો',
    modelUsed: 'એઆઈ અનુમાન મૉડલ',
    lpSolver: 'ઓપ્ટિમાઇઝેશન સૉલ્વર',
    fairnessScore: 'ન્યાયીપણાનું માપ',
    rawCodes: 'કારણ કોડ્સ',

    // Farmer Scenario Configuration
    startWaterSharingTitle: '💧 પાણી વહેંચણી શરૂ કરો',
    startWaterSharingSubtitle: 'પાણીની પરિસ્થિતિ જણાવો, અમે યોગ્ય વહેંચણી યોજના શોધીશું.',
    q1SituationTitle: '💧 આજે પાણીની સ્થિતિ કેવી છે?',
    q1OptEnoughTitle: '💧 પૂરતું પાણી',
    q1OptEnoughDesc: 'ખેડૂતો માટે પૂરતું પાણી ઉપલબ્ધ છે.',
    q1OptSomeShortageTitle: '💧 થોડી અછત',
    q1OptSomeShortageDesc: 'ખેડૂતોની જરૂરિયાત કરતાં ઓછું પાણી છે.',
    q1OptSeriousShortageTitle: '🚨 ગંભીર અછત',
    q1OptSeriousShortageDesc: 'ખેડૂતોની જરૂરિયાત કરતાં ઘણું ઓછું પાણી છે.',
    q1OptCropsUrgentTitle: '🌱 પાકને તાત્કાલિક પાણી જોઈએ છે',
    q1OptCropsUrgentDesc: 'પાક પાણીની તીવ્ર અછતમાં છે અને તાત્કાલિક જરૂર છે.',
    q2FarmersTitle: '👨‍🌾 કેટલા ખેડૂતો પાણી વહેંચી રહ્યા છે?',
    q2FarmersLabel: 'પાણી વહેંચતા ખેડૂતો',
    q2FarmersHelper: 'જણાવો કે કેટલા ખેડૂતો આ પાણીનો ઉપયોગ કરે છે.',
    q5WaterAvailableTitle: '💦 કેટલું પાણી ઉપલબ્ધ છે?',
    q5WaterAvailableHelper: 'વૈકલ્પિક — સામાન્ય પાણી પુરવઠો વાપરવા માટે ખાલી રાખો.',
    q5UnknownCheckbox: 'મને ચોક્કસ જથ્થો ખબર નથી',
    farmerConfigUsageNote: 'તમારી માહિતીનો ઉપયોગ પાણી વહેંચણી યોજના બનાવવા માટે થાય છે.',
    findWaterPlanBtn: '💧 પાણી વહેંચણી યોજના શોધો',
    findWaterPlanBtnHelper: 'અમે પાકની જરૂરિયાત, તકરાર અને ન્યાયી વહેંચણી તપાસીશું.',
    findingWaterPlanTitle: '💧 પાણી વહેંચણી યોજના શોધાઈ રહી છે',
    findingStage1: '🌱 પાકની પાણીની જરૂરિયાત તપાસાઈ રહી છે',
    findingStage2: '💧 ઉપલબ્ધ પાણીની તપાસ થઈ રહી છે',
    findingStage3: '⚠️ પાણીની સમસ્યાઓ ઓળખાઈ રહી છે',
    findingStage4: '⚖️ ઉપલબ્ધ પાણીની ન્યાયી વહેંચણી થઈ રહી છે',
    findingStage5: '🤝 આખરી સહમતિ ચકાસાઈ રહી છે',

    // Explainability Page
    explainPageTitleFarmer: '💧 મને આટલું પાણી કેમ મળ્યું?',
    explainPageSubtitleFarmer: 'AquaMediAI એ વહેંચણી યોજના તૈયાર કરતા પહેલાં ઉપલબ્ધ પાણી, પાકની જરૂરિયાતો અને અન્ય ખેડૂતોની જરૂરિયાતો ધ્યાનમાં લીધી હતી.',
    explainResultCardTitle: '💧 તમારું પાણી વહેંચણી પરિણામ',
    explainWhySectionTitle: '💡 મને આટલું પાણી કેમ મળ્યું?',
    explainConflictSectionTitle: '⚠️ પાણી વહેંચણી પર શેની અસર પડી?',
    explainFairnessSectionTitle: '⚖️ શું વહેંચણી ન્યાયી હતી?',
    explainFairnessText: 'ઉપલબ્ધ પાણીની વહેંચણી કરતી વખતે ન્યાયીપણાનું ધ્યાન રાખવામાં આવ્યું હતું.',
    explainNegotiationSectionTitle: '🤝 યોજના પર સહમતિ કેવી રીતે સધાઈ?',
    explainNegotiationText1: 'સિસ્ટમના ખેડૂત એજન્ટોએ સૂચવેલ પાણી ફાળવણીનું મૂલ્યાંકન કર્યું.',
    explainNegotiationText2: 'જો સૂચવેલ ફાળવણી જરૂરી શરતો પૂરી ન કરતી હોય, તો મધ્યસ્થી પ્રક્રિયાએ સુધારાઓનું મૂલ્યાંકન કર્યું.',
    explainNegotiationText3: 'દરેક સુધારેલી ફાળવણી પાણીની મર્યાદાઓ સામે ચકાસવામાં આવી હતી.',
    explainExpertPageTitle: '🔬 નિર્ણય સમજૂતી',
    explainExpertPageSubtitle: 'તપાસો કે AquaMediAI અંદાજિત પાણીની માંગથી અંતિમ સહમતિ સુધી કેવી રીતે પહોંચ્યું.',
    shapUnavailableText: 'આ અનુમાન માટે વિગતવાર ફીચર યોગદાન ઉપલબ્ધ નહોતું.',
    farmerPortalTitle: 'મારા ખેતરની પાણીની જરૂરિયાત ચકાસો',
    farmerPortalDesc: 'આજના માટે AI-ગણતરી કરેલ પાણીની માંગનો અંદાજ મેળવવા માટે નીચે તમારા ખેતરની વિગતો દાખલ કરો.',
    welcomePortalTitle: 'કૃષિ નિર્ણય સહાયક પ્રણાલી',
    welcomePortalSubtitle: 'સરકારી સ્તરની જળ વિવાદ મધ્યસ્થતા અને પાક સ્વાસ્થ્ય બુદ્ધિ',
    welcomeRolePrompt: 'આગળ વધવા માટે તમારું પોર્ટલ સ્તર પસંદ કરો:',
    farmerCardTitle: 'ખેડૂત પ્રવેશ',
    farmerCardBadge: 'તાત્કાલિક પ્રવેશ • કોઈ પાસવર્ડની જરૂર નથી',
    farmerCardDesc: 'દૈનિક પાકની પાણીની માંગ, સિંચાઈ માર્ગદર્શન અને હવામાનની માહિતી તરત જુઓ.',
    farmerCardBtn: 'ખેડૂત તરીકે આગળ વધો',
    expertCardTitle: 'કૃષિ નિષ્ણાત પ્રવેશ',
    expertCardBadge: 'સત્તાવાર પ્રમાણીકરણ જરૂરી',
    expertCardDesc: 'કૃષિ અધિકારીઓ અને મધ્યસ્થીઓ માટે. મલ્ટી-એજન્ટ મધ્યસ્થતા અને મોડેલ વિશ્લેષણ મેળવો.',
    expertCardBtn: 'કૃષિ નિષ્ણાત તરીકે લૉગિન કરો',
    loginTitle: 'કૃષિ નિષ્ણાત લૉગિન',
    loginSubtitle: 'મધ્યસ્થતા સિસ્ટમમાં પ્રવેશવા માટે ઓળખપત્ર દાખલ કરો',
    loginEmailLabel: 'વપરાશકર્તા નામ અથવા સત્તાવાર ઇમેઇલ',
    loginPasswordLabel: 'પાસવર્ડ',
    loginSubmitBtn: 'પ્રમાણિત કરો અને પ્રવેશ કરો',
    loginBackBtn: 'પાછા જાઓ',
    activeModelLabel: 'સક્રિય અનુમાન મૉડલ: XGBoost (ચકાસાયેલ ઉત્પાદન)',
    governmentBadge: 'કૃષિ અને જળ સંસાધન વિભાગ • સત્તાવાર પ્લેટફોર્મ',
    logoutBtn: 'લૉગઆઉટ',
    farmerModeActive: 'ખેડૂત ગેસ્ટ મોડ',
    expertModeActive: 'કૃષિ વિસ્તરણ અધિકારી',
  },

  mr: {
    appTitle: 'AquaMediAI',
    appSubtitle: 'जल वाटप साहाय्यक',
    farmerView: '👨‍🌾 शेतकरी दृश्य',
    expertView: '🔬 तज्ज्ञ दृश्य',
    waterConflictMonitor: 'जल संघर्ष निरीक्षक',
    waterConflictsFound: 'पाणी वाटपातील समस्या आढळल्या',
    mostUrgentIssue: 'सर्वात महत्त्वाची समस्या',
    waterShortage: 'पाण्याची कमतरता',
    availableWaterVsFarmDemand: 'उपलब्ध पाणी विरूद्ध शेतीची मागणी',
    overlappingIrrigationSchedules: 'एकाच वेळी सिंचन वेळापत्रक',
    highWaterPriority: 'उच्च पाणी प्राधान्य',
    farmsInvolved: 'समाविष्ट शेतकरी',
    whyThisIssueWasFlagged: 'ही समस्या का नोंदवली गेली',
    waterPriorityScore: 'पाणी प्राधान्य गुण',
    cropWaterSensitivity: 'पिकाची पाणी संवेदनशीलता',
    growthStageImportance: 'वाढ टप्प्याचे महत्त्व',
    overallPriority: 'एकूण प्राधान्य',
    waterShortageDesc: 'उपलब्ध पाण्याचे प्रमाण सर्व शेतकऱ्यांच्या मागणीपेक्षा कमी होते.',
    apiConnected: 'एपीआय जोडले आहे',
    backendOffline: 'बॅकएंड ऑफलाइन',
    checkingApi: 'तपासत आहे...',

    myWaterSharing: '💧 माझे पाणी वाटप',
    myWaterSharingDesc: 'तुमच्या पिकासाठी पाण्याच्या वाटपाचे स्पष्ट व सोपे दृश्य.',
    selectFarmer: 'शेतकरी निवडा',
    viewingFor: 'यांच्यासाठी पाणी माहिती पाहत आहात',
    noScenarioTitle: 'कोणतीही पाणी योजना उपलब्ध नाही',
    noScenarioDesc: 'पाणी वाटप पाहण्यासाठी नवीन योजना सुरू करा.',
    startScenarioBtn: 'पाणी वाटप योजना सुरू करा',

    waterGivenToMe: '💧 मला मिळालेले पाणी',
    waterGivenDesc: 'हे तुम्हाला वाटप केलेले पाणी आहे.',
    waterNeeded: '🌱 लागणारे पाणी',
    waterNeededDesc: 'तुमच्या पिकासाठी अंदाजे लागणारे पाणी.',
    waterAvailable: '💦 उपलब्ध पाणी',
    waterAvailableDesc: 'सर्व शेतकऱ्यांसाठी कालव्यात उपलब्ध एकूण पाणी.',
    sharingResult: '🤝 वाटप निकाल',
    sharingResultDesc: 'पाणी वाटप कसे ठरले ते पहा.',

    yourResultTitle: '💧 तुमचे पाणी वाटप निकाल',
    requestedLabel: 'मागितलेले पाणी',
    receivedLabel: 'मिळालेले पाणी',
    satisfiedLabel: 'समाधान प्रमाण',
    surplusNote: 'पाणी पुरेसे असल्याने पूर्ण मागणी मंजूर झाली.',
    shortageNote: 'पाण्याच्या तुटवड्यामुळे सर्वांना समप्रमाणात वाटप करण्यात आले.',
    agreementReachedNote: 'सर्व शेतकऱ्यांमध्ये एकमत झाले.',
    agreementPendingNote: 'वाटप योजनेवर अंतिम संमती अपेक्षित आहे.',

    whyTitle: '💡 मला एवढे पाणी का मिळाले?',
    whySubtitle: 'तुमचे वाटप पिकाची गरज, उपलब्धता आणि नियमांनुसार ठरवले गेले.',

    reasonResourceShortageTitle: 'पाण्याची कमतरता',
    reasonResourceShortageDesc: 'एकूण पाणी मागणीपेक्षा कमी असल्याने वाटप प्रमाणात केले गेले.',
    reasonHighUrgencyTitle: 'पिकाची तातडीची गरज',
    reasonHighUrgencyDesc: 'पिकाच्या नाजूक अवस्थेमुळे या पिकाला प्राधान्य दिले गेले.',
    reasonHighCropSensitivityTitle: 'पाणी संवेदनशील पीक',
    reasonHighCropSensitivityDesc: 'हे पीक पाण्याशिवाय तग धरू शकत नसल्याने संरक्षण दिले गेले.',
    reasonMinimumRequirementTitle: 'किमान पाण्याची हमी',
    reasonMinimumRequirementDesc: 'पिकाचे नुकसान टाळण्यासाठी आवश्यक किमान पाणी दिले गेले.',
    reasonMaximumRequirementTitle: 'कमाल मर्यादा',
    reasonMaximumRequirementDesc: 'पाण्याचा अपव्यय टाळण्यासाठी कमाल मर्यादेत पाणी दिले गेले.',
    reasonCanalCapacityTitle: 'कालवा क्षमता मर्यादा',
    reasonCanalCapacityDesc: 'कालव्यातून पाणी सोडण्याच्या मर्यादेनुसार नियोजन केले गेले.',
    reasonWindowConflictTitle: 'वेळेचा ताळमेळ',
    reasonWindowConflictDesc: 'एकाच वेळी मागणी आल्यामुळे पाण्याचे तास विभागले गेले.',
    reasonFairnessAdjustmentTitle: 'न्यायी वाटप समायोजन',
    reasonFairnessAdjustmentDesc: 'सर्व शेतकऱ्यांना पाण्याचा योग्य हिस्सा मिळावा म्हणून समायोजन केले गेले.',
    reasonNegotiationConcessionTitle: 'परस्पर सहमतीने तडजोड',
    reasonNegotiationConcessionDesc: 'शेतकऱ्यांनी सहकार्याने थोडी तडजोड स्वीकारली.',
    reasonBatnaProtectionTitle: 'शेतकरी हक्क संरक्षण',
    reasonBatnaProtectionDesc: 'कोणत्याही शेतकऱ्याचे नुकसान होणार नाही याची खात्री केली गेली.',
    reasonUnmetDemandTitle: 'अपूर्ण मागणी',
    reasonUnmetDemandDesc: 'तुटवड्यामुळे काही मागणी अपूर्ण राहिली.',
    reasonFullSatisfactionTitle: 'पूर्ण मागणी मंजूर',
    reasonFullSatisfactionDesc: 'पिकासाठी लागणारे १००% पाणी मंजूर झाले आहे.',
    reasonWaterSurplusTitle: 'अतिरिक्त पाणी उपलब्ध',
    reasonWaterSurplusDesc: 'मागणीपेक्षा पाणी जास्त उपलब्ध होते.',

    conflictSectionTitle: '⚠️ पाणी वाटपातील समस्या',
    conflictSectionSubtitle: 'पाणी नियोजन करताना खालील बाबींची काळजी घेतली गेली.',
    noConflictsFound: 'कोणतीही समस्या नाही — पाणी पुरवठा सुरळीत आहे.',
    conflictWaterShortage: 'पाण्याची कमतरता',
    conflictWaterShortageDesc: 'उपलब्ध पाणी सर्व शेतकऱ्यांच्या मागणीपेक्षा कमी होते.',
    conflictWindowOverlap: 'एकाच वेळी सिंचनाची वेळ',
    conflictWindowOverlapDesc: 'अनेक शेतकऱ्यांनी एकाच वेळी पाणी मागितले होते.',
    conflictCanalCapacity: 'कालवा मर्यादा',
    conflictCanalCapacityDesc: 'कालव्याची पाणी वाहून नेण्याची क्षमता मर्यादित आहे.',
    conflictMinRequirement: 'किमान गरज',
    conflictMinRequirementDesc: 'किमान आवश्यक पाणी पुरवठा सुरक्षित करण्यात आला.',
    conflictHighCropStress: 'पिकाचा पाण्याचा ताण',
    conflictHighCropStressDesc: 'काही पिकांवर पाण्याचा जास्त ताण होता.',
    conflictTimingDetected: 'सिंचन वेळेची समस्या',
    conflictSingularDetected: '१ समस्या आढळली',
    conflictPluralDetected: 'समस्या आढळल्या',
    whatHappened: 'काय घडले?',
    whyItMatters: 'याचे काय परिणाम होतात?',

    howSharedTitle: '🤝 पाणी कसे वाटप झाले?',
    howSharedSubtitle: 'न्यायी व समतोल पाणी वाटपाची प्रक्रिया.',
    step1: '१. पिकांची गरज मोजली',
    step1Desc: 'प्रत्येक पिकासाठी हवामान व क्षेत्रानुसार पाण्याची मागणी काढली.',
    step2: '२. उपलब्ध पाणी तपासले',
    step2Desc: 'कालव्यात किती पाणी उपलब्ध आहे याची खातरजमा केली.',
    step3: '३. समस्यांची ओळख पटवली',
    step3Desc: 'तुटवडा आणि वेळेच्या अडचणी शोधल्या.',
    step4: '४. संगणकीय वाटप केले',
    step4Desc: 'गणिती सूत्रांद्वारे सर्वांना न्यायी हिस्सा निश्चित केला.',
    step5: '५. परस्पर सहमती साध्य केली',
    step5Desc: 'सर्व शेतकरी घटकांचे समाधान तपासून योजना अंतिम केली.',

    fairSharingTitle: '⚖️ न्यायी पाणी वाटप',
    fairSharingDesc: 'सर्व शेतकऱ्यांना त्यांच्या पिकाच्या गरजेनुसार पाणी मिळाले.',
    fairSharingNote: 'लहान आणि मोठ्या शेतकऱ्यांमध्ये कोणताही भेदभाव केला जात नाही.',

    techDetailsTitle: 'तांत्रिक माहिती',
    techDetailsSubtitle: 'तज्ज्ञांसाठी तपशीलवार माहिती',
    modelUsed: 'एआय अंदाज मॉडेल',
    lpSolver: 'ऑप्टिमायझेशन सॉल्व्हर',
    fairnessScore: 'न्यायीपणा गुणांक',
    rawCodes: 'रीझन कोड्स',

    startWaterSharingTitle: '💧 पाणी वाटप नियोजन',
    startWaterSharingSubtitle: 'पाण्याची परिस्थिती निवडा, आम्ही योग्य वाटप योजना तयार करू.',
    q1SituationTitle: '💧 आज पाण्याची परिस्थिती कशी आहे?',
    q1OptEnoughTitle: '💧 पुरेसे पाणी',
    q1OptEnoughDesc: 'सर्व शेतकऱ्यांसाठी पुरेसे पाणी उपलब्ध आहे.',
    q1OptSomeShortageTitle: '💧 थोडी कमतरता',
    q1OptSomeShortageDesc: 'मागणीपेक्षा थोडे कमी पाणी उपलब्ध आहे.',
    q1OptSeriousShortageTitle: '🚨 तीव्र टंचाई',
    q1OptSeriousShortageDesc: 'पाणी खूप कमी असून जपून वापरावे लागेल.',
    q1OptCropsUrgentTitle: '🌱 पिकांना तातडीची गरज',
    q1OptCropsUrgentDesc: 'काही पिकांना त्वरित पाण्याची गरज आहे.',
    q2FarmersTitle: '👨‍🌾 पाणी वाटपात किती शेतकरी आहेत?',
    q2FarmersLabel: 'शेतकऱ्यांची संख्या',
    q2FarmersHelper: 'कालव्यावर अवलंबून असलेल्या शेतकऱ्यांची संख्या निवडा.',
    q5WaterAvailableTitle: '💦 किती पाणी उपलब्ध आहे?',
    q5WaterAvailableHelper: 'ऐच्छिक — मानक पाणी पुरवठ्यासाठी रिकामे ठेवा.',
    q5UnknownCheckbox: 'मला नेमके प्रमाण माहीत नाही',
    farmerConfigUsageNote: 'तुमच्या माहितीचा वापर योग्य नियोजन करण्यासाठी केला जातो.',
    findWaterPlanBtn: '💧 पाणी वाटप योजना शोधा',
    findWaterPlanBtnHelper: 'पिकांची गरज आणि न्यायी वाटपाचा हिशोब केला जाईल.',
    findingWaterPlanTitle: '💧 योजना तयार होत आहे...',
    findingStage1: '🌱 पिकांची पाण्याची गरज मोजत आहे',
    findingStage2: '💧 उपलब्ध पाणी तपासत आहे',
    findingStage3: '⚠️ अडचणी शोधत आहे',
    findingStage4: '⚖️ न्यायी वाटप तयार करत आहे',
    findingStage5: '🤝 अंतिम सहमती तपासत आहे',

    explainPageTitleFarmer: '💧 मला एवढे पाणी का मिळाले?',
    explainPageSubtitleFarmer: 'पिकाची गरज, हवामान आणि उपलब्ध पाण्याचा विचार करून हे वाटप करण्यात आले.',
    explainResultCardTitle: '💧 तुमचे पाणी वाटप निकाल',
    explainWhySectionTitle: '💡 पाणी वाटपाचे कारण',
    explainConflictSectionTitle: '⚠️ कशामुळे परिणाम झाला?',
    explainFairnessSectionTitle: '⚖️ वाटप योग्य आहे का?',
    explainFairnessText: 'सर्व शेतकऱ्यांच्या हिताचा विचार करून समतोल वाटप केले गेले.',
    explainNegotiationSectionTitle: '🤝 निर्णय कसा झाला?',
    explainNegotiationText1: 'प्रत्येक शेतकऱ्याच्या गरजेची नोंद घेण्यात आली.',
    explainNegotiationText2: 'तुटवडा असल्यास समान कपात लागू करण्यात आली.',
    explainNegotiationText3: 'पाणी मर्यादांचे तंतोतंत पालन केले गेले.',
    explainExpertPageTitle: '🔬 निर्णय विश्लेषण',
    explainExpertPageSubtitle: 'अंदाज ते अंतिम निर्णयापर्यंतची सर्व सांख्यिकी माहिती.',
    shapUnavailableText: 'तपशीलवार विश्लेषण उपलब्ध नाही.',

    farmerPortalTitle: 'माझ्या शेताची पाण्याची गरज तपासा',
    farmerPortalDesc: 'आजच्या पिकासाठी लागणाऱ्या पाण्याचा अंदाज घेण्यासाठी शेताचा तपशील भरा.',

    welcomePortalTitle: 'कृषी निर्णय साहाय्य प्रणाली',
    welcomePortalSubtitle: 'शासकीय दर्जाची जल विवाद मध्यस्थी व पीक आरोग्य बुद्धिमत्ता',
    welcomeRolePrompt: 'कृपया पुढे जाण्यासाठी तुमचा प्रवेश स्तर निवडा:',
    farmerCardTitle: 'शेतकरी प्रवेश',
    farmerCardBadge: 'सुलभ प्रवेश • कोणताही पासवर्ड नको',
    farmerCardDesc: 'दैनिक पीक पाणी मागणी अंदाज, सिंचन मार्गदर्शन आणि हवामान सल्ला त्वरित पहा.',
    farmerCardBtn: 'शेतकरी म्हणून पुढे जा',
    expertCardTitle: 'कृषी तज्ज्ञ प्रवेश',
    expertCardBadge: 'शासकीय प्रमाणीकरण आवश्यक',
    expertCardDesc: 'कृषी विस्तार अधिकारी व मध्यस्थांसाठी. बहु-एजंट मध्यस्थी आणि मॉडेल कार्यक्षमतेचे विश्लेषण करा.',
    expertCardBtn: 'कृषी तज्ज्ञ म्हणून लॉगिन करा',
    loginTitle: 'कृषी तज्ज्ञ लॉगिन',
    loginSubtitle: 'मध्यस्थी प्रणालीमध्ये प्रवेश करण्यासाठी तुमची अधिकृत माहिती भरा',
    loginEmailLabel: 'वापरकर्ता नाव किंवा अधिकृत ईमेल',
    loginPasswordLabel: 'पासवर्ड',
    loginSubmitBtn: 'प्रमाणित करा व प्रवेश करा',
    loginBackBtn: 'मागे जा',
    activeModelLabel: 'सक्रिय अंदाज मॉडेल: XGBoost (प्रमाणित उत्पादन मॉडेल)',
    governmentBadge: 'कृषी व जलसंपदा विभाग • अधिकृत व्यासपीठ',
    logoutBtn: 'लॉगआउट',
    farmerModeActive: 'शेतकरी गेस्ट मोड',
    expertModeActive: 'कृषी विस्तार अधिकारी',
  },
};
