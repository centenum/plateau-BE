import marshmallow as ma

class ArrestHistorySchema(ma.Schema):
    arrested = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class CriminalOffenceSchema(ma.Schema):
    tried = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class LunacyInquirySchema(ma.Schema):
    tried = ma.fields.Boolean()
    optionConclusion = ma.fields.String()


class BankruptcyEnquirySchema(ma.Schema):
    bankruptcyInvolvment = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class PoliticalPartySchema(ma.Schema):
    isPartyMember = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class PartySponsorSchema(ma.Schema):
    partyIsSponsoring = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class TaxHistorySchema(ma.Schema):
    threeYearsCompletion = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class DrugHistorySchema(ma.Schema):
    beenOnDrugs = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class IsVotedSchema(ma.Schema):
    isRegisteredVoter = ma.fields.Boolean()
    optionConclusion = ma.fields.String()

class InstitutionSchema(ma.Schema):
    institutionName = ma.fields.String()
    institutionType = ma.fields.String()
    institutionStartDate = ma.fields.Date()
    institutionEndDate = ma.fields.Date()

class EducationExperienceSchema(ma.Schema):
    experience = ma.fields.String()
    qualification = ma.fields.String()
    institutionName = ma.fields.String()
    obtainDate = ma.fields.Date()

class WorkExperienceSchema(ma.Schema):
    qualification = ma.fields.String()
    companyName = ma.fields.String()
    startDate = ma.fields.Date()
    endDate = ma.fields.Date()
    tillPresent = ma.fields.Boolean()

class NominatorSchema(ma.Schema):
    firstName = ma.fields.String()
    lastName = ma.fields.String()
    address = ma.fields.String()
    occupation = ma.fields.String()
    localGovernment = ma.fields.String()
    ward = ma.fields.String()
    signature = ma.fields.String()

class DocumentSchema(ma.Schema):
    curriculumVitae = ma.fields.String()
    nationalIdentificationSlip = ma.fields.String()
    birthCertificate = ma.fields.String()
    partyMembershipCard = ma.fields.String()
    voterCard = ma.fields.String()
    educationertificate = ma.fields.String()
    letterOfDisengagement = ma.fields.String()
    taxClearance = ma.fields.String()

class PoliticalExperienceSchema(ma.Schema):
    experience = ma.fields.String()
    

class ChairmanSchema(ma.Schema):
    firstName = ma.fields.String(required=True)
    lastName = ma.fields.String(required=True)
    address = ma.fields.String(required=True)
    occupation = ma.fields.String(required=True)
    localGovernment = ma.fields.String(required=True)
    otherNames = ma.fields.String()
    maidenName = ma.fields.String()
    changedName = ma.fields.String()
    residentialAddress = ma.fields.String(required=True)
    maritalStatus = ma.fields.String(required=True)
    postalAddress = ma.fields.String(required=True)
    nationality = ma.fields.String(required=True)
    birthPlace = ma.fields.String(required=True)
    birthDate = ma.fields.Date(required=True)
    state = ma.fields.String(required=True)
    indigeneOfPresentPlace = ma.fields.Boolean(required=True)
    ward = ma.fields.String()
    presentPlaceStayDuration = ma.fields.String()
    criminalOffenseTrial = ma.fields.Nested(CriminalOffenceSchema)
    conductTribunalTrial = ma.fields.Nested(LunacyInquirySchema, required=True)
    bankruptcyEnquiry = ma.fields.Nested(BankruptcyEnquirySchema, required=True)
    arrestHistory = ma.fields.Nested(ArrestHistorySchema, required=True)
    politicalPartyData = ma.fields.Nested(PoliticalPartySchema, required=True)
    partySponsorData = ma.fields.Nested(PartySponsorSchema)
    taxHistoryData = ma.fields.Nested(TaxHistorySchema)
    drugHistoryData = ma.fields.Nested(DrugHistorySchema)
    voteData = ma.fields.Nested(IsVotedSchema)
    institutionData = ma.fields.Nested(InstitutionSchema, many=True)
    educationQualificationData = ma.fields.Nested(EducationExperienceSchema, many=True)
    lunacyInquiryTrial = ma.fields.Nested(LunacyInquirySchema, required=True)
    workExperienceData = ma.fields.Nested(WorkExperienceSchema, many=True)
    politicalExperienceData = ma.fields.Nested(PoliticalExperienceSchema, many=True)
    oath = ma.fields.String()
    surname = ma.fields.String()
    pastClubsOrSocieties = ma.fields.String()
    contestingReason = ma.fields.String()
    sponsor = ma.fields.String()
    nominators = ma.fields.Nested(NominatorSchema, many=True)
    documents = ma.fields.Nested(DocumentSchema)
    otherNationality = ma.fields.String()


class GenerateChairmanWithDeputySchema(ma.Schema):
    chairman = ma.fields.Nested(ChairmanSchema, required=True)
    deputyChairman = ma.fields.Nested(ChairmanSchema, required=True)


class CouncillorSchema(ma.Schema):
    firstName = ma.fields.String(required=True)
    lastName = ma.fields.String(required=True)
    otherNames = ma.fields.String()
    residentialAddress = ma.fields.String(required=True)
    address = ma.fields.String(required=True)
    occupation = ma.fields.String(required=True)
    localGovernment = ma.fields.String(required=True)
    surname = ma.fields.String(required=True)
    birthDate = ma.fields.Date(required=True)
    ward = ma.fields.String(required=True)
    state = ma.fields.String(required=True)
    nationality = ma.fields.String(required=True)
    institutionData = ma.fields.Nested(InstitutionSchema, many=True)
    sponsor = ma.fields.String()
    nominators = ma.fields.Nested(NominatorSchema, many=True)
    oath = ma.fields.String()
    otherNationality = ma.fields.String()
    
    
class UpdateStatusSchema(ma.Schema):
    _id = ma.fields.String(required=True)
    status = ma.fields.String(required=True, validate=ma.validate.OneOf(['approved', 'rejected']))
    
