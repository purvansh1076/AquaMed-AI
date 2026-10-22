/**
 * Centralized Internationalization (i18n) for AquaMediAI Farmer View
 * Supported Languages: English (en), हिन्दी (hi), ગુજરાતી (gu)
 *
 * All translations are localized for agricultural clarity and simplicity.
 * No external translation APIs are used.
 */

export type Language = 'en' | 'hi' | 'gu';

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
  },
};
