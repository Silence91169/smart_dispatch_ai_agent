"""Template library of emergency incident archetypes for call generation."""

from __future__ import annotations

from dataclasses import dataclass, field

from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity


@dataclass
class IncidentTemplate:
    """A reusable emergency archetype rendered into varied Delhi-context transcripts.

    Attributes:
        template_id: Unique identifier, e.g. ``house_fire_residential``.
        incident_type: The :class:`IncidentType` enum value.
        default_severity: Default :class:`Severity`.
        resources_needed: List of resource types to dispatch.
        transcript_variants: List of strings with ``{location}``, ``{detail}``,
            and ``{panic}`` placeholders.  ~70% English, ~30% Hinglish.
        detail_pool: Small detail strings that fill ``{detail}``.
        panic_phrases: Opener phrases that fill ``{panic}``.
    """

    template_id: str
    incident_type: IncidentType
    default_severity: Severity
    resources_needed: list[ResourceType]
    transcript_variants: list[str]
    detail_pool: list[str] = field(default_factory=list)
    panic_phrases: list[str] = field(default_factory=list)


_TEMPLATES: list[IncidentTemplate] = [
    IncidentTemplate(
        template_id="house_fire_residential",
        incident_type=IncidentType.FIRE,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.FIRE_TRUCK, ResourceType.AMBULANCE],
        transcript_variants=[
            "There's a house on fire at {location}! The whole second floor is engulfed, flames are shooting out the windows!",
            "Mera ghar jal raha hai! {location} pe aao jaldi, I don't know if everyone got out!",
            "{panic} house fire at {location}. {detail}. Fire brigade ko bhejo abhi!",
            "I can see a structure fire from the road near {location}. The smoke is black and thick, the whole roof is going.",
            "Arre bhai {location} pe ek ghar mein aag lag gayi hai, {detail}, flames spreading to neighbouring house!",
            "Fire department jaldi aao, {location}, ek ghar mein aag hai. {detail}.",
            "Huge fire at {location}, the house is fully involved. {detail}. I can feel the heat from across the street.",
        ],
        detail_pool=[
            "I can hear someone inside shouting",
            "the cylinder bhi andar hai, could blast",
            "the fire is spreading to the fence",
            "children might be inside, bacche hain andar",
            "bijli ka short circuit hua shayad",
            "neighbour's tree is also catching fire",
            "I can't reach the family on phone",
            "the roof has already partially collapsed",
        ],
        panic_phrases=[
            "oh my god", "hey bhagwan", "please help", "arre arre",
            "jaldi aao", "bachao please",
        ],
    ),
    IncidentTemplate(
        template_id="apartment_fire_highrise",
        incident_type=IncidentType.FIRE,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.FIRE_TRUCK, ResourceType.AMBULANCE],
        transcript_variants=[
            "Fire in a high-rise apartment at {location}! The hallway on my floor is full of smoke!",
            "{panic} fire alarm baj raha hai {location} pe aur lift mein se dhuan aa raha hai — yeh serious hai!",
            "Main upper floor pe trapped hoon {location} mein, stairwell blocked hai smoke se. Families hain yahan!",
            "Apartment complex mein aag lagi hai {location} pe. {detail}. Multiple floors, ladders chahiye.",
            "We evacuated {location} but people are still inside. Fire looks like it started on third floor. {detail}.",
            "Smoke pouring out the windows at the apartments on {location}. I can see flames on two floors.",
            "{panic} Main 8th floor pe hoon {location} ka aur hallway mein aag hai. {detail}.",
        ],
        detail_pool=[
            "the lift band ho gayi hai",
            "families with children are on upper floors",
            "kisi ne bola gas smell aa rahi thi before it started",
            "one person is already on the fire escape",
            "sprinklers are not working",
            "ek budhiya hai paas mein jo chal nahi sakti",
            "I can hear people shouting and knocking upstairs",
        ],
        panic_phrases=[
            "hey bhagwan", "please", "hum trapped hain", "help us please",
            "bachao", "please jaldi aao",
        ],
    ),
    IncidentTemplate(
        template_id="cardiac_arrest",
        incident_type=IncidentType.MEDICAL,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.AMBULANCE],
        transcript_variants=[
            "oh my god mere pati breathe nahi kar rahe, please help, we're at {location}",
            "Mujhe ambulance chahiye abhi {location} pe, {detail}, wo unresponsive hain!",
            "hello?? {location} ke paas ek banda collapse ho gaya, I don't think he has a pulse. {detail}.",
            "please jaldi aao, {location} pe ek aadmi pada hua hai, hil nahi raha, hont neele ho rahe hain",
            "{panic} cardiac emergency at {location}, hum CPR kar rahe hain, send help immediately",
            "Aunty ji gir gayi hain {location} ke bahar aur breathe nahi kar rahi. {detail}. Jaldi aao please.",
            "Person collapsed at {location}, unconscious, no pulse, CPR shuru kar diya. {detail}. AED chahiye.",
        ],
        detail_pool=[
            "abhi CPR kar rahe hain",
            "unhone chest pakad ke gira tha",
            "woh chest pain complain kar rahi thi phir gir gayi",
            "completely unresponsive hai, hilane pe bhi nahi uta",
            "CPR nahi aata, koi try kar raha hai",
            "bahut dheere breathe kar raha hai",
            "kaafi der se pada lag raha hai",
        ],
        panic_phrases=[
            "hey bhagwan", "please please", "help karo", "jaldi warna marenge",
            "bachao", "koi doctor hai?",
        ],
    ),
    IncidentTemplate(
        template_id="car_accident_injury",
        incident_type=IncidentType.ACCIDENT,
        default_severity=Severity.HIGH,
        resources_needed=[ResourceType.AMBULANCE, ResourceType.POLICE_CAR],
        transcript_variants=[
            "Car accident at {location}, multiple vehicles, I can see injured people. {detail}.",
            "Bahut bura accident hua hai {location} pe, ek gaadi ne red light tod di. {detail}. Help chahiye.",
            "{panic} accident at {location}, car vs auto, {detail}",
            "Serious accident near {location}. Someone is trapped inside one of the vehicles.",
            "Multi-vehicle accident at {location}. Khoon dikh raha hai. {detail}. Ambulance aur police bhejo.",
            "Collision at {location}, airbags deployed, at least one person not moving. {detail}.",
            "Truck ne {location} pe ek scooty ko mara. {detail}. Scooty wala badly injured.",
        ],
        detail_pool=[
            "ek aadmi steering pe jhuka hua hai",
            "ek aurat ke sir se khoon aa raha hai",
            "driver bahar nahi nikal pa raha",
            "peeche seat pe ek bacha hai, ro raha hai",
            "ek gaadi mein hood ke neeche chhoti aag hai",
            "windshield completely toot gayi hai",
            "someone conscious hai but pinned under the vehicle",
        ],
        panic_phrases=[
            "oh no", "yeh bahut bura hai", "please hurry", "arre bhai",
        ],
    ),
    IncidentTemplate(
        template_id="car_accident_minor",
        incident_type=IncidentType.ACCIDENT,
        default_severity=Severity.MEDIUM,
        resources_needed=[ResourceType.POLICE_CAR],
        transcript_variants=[
            "Minor accident at {location}, no injuries that I can see. Two cars. {detail}.",
            "Car accident at {location}, both drivers bahar hain aur theek lagte hain. {detail}.",
            "Small crash near {location}, cars are blocking traffic but everyone seems okay.",
            "Bhai {location} pe do gaadiyaan takra gayi hain, koi hurt nahi hua but argument ho raha hai.",
            "Traffic accident at {location}, just bumper damage. {detail}. Police report chahiye.",
            "Cars collided at {location}, no injuries, property damage only. {detail}.",
        ],
        detail_pool=[
            "ek bumper latkaa hua hai",
            "insurance ke liye report chahiye",
            "ek driver thoda shaken up hai",
            "ek lane block ho gayi hai",
            "gaadiyaan drive nahi ho sakti",
            "dono drivers phone pe hain",
        ],
        panic_phrases=[
            "hello", "sorry to disturb", "um", "bhai",
        ],
    ),
    IncidentTemplate(
        template_id="armed_robbery",
        incident_type=IncidentType.CRIME,
        default_severity=Severity.HIGH,
        resources_needed=[ResourceType.POLICE_CAR],
        transcript_variants=[
            "Armed robbery in progress at {location}! {detail}. Police bhejo abhi!",
            "{location} pe koi loot raha hai, weapon hai uske paas! {detail}.",
            "{panic} robbery at {location}, {detail}, jaldi bhejo!",
            "I just saw a robbery at {location}. Attacker had a knife. They ran toward {detail}.",
            "Loot ho rahi hai {location} pe, banda bhaag gaya. {detail}.",
            "Man pulled a knife inside {location} and demanded money. {detail}. They just left.",
            "Chain snatching at {location}! They had a weapon. {detail}.",
        ],
        detail_pool=[
            "abhi bhi uske paas weapon hai",
            "suspect ne red hoodie pahni hai",
            "do log the, dono ne munh dhaka hua tha",
            "north side bhaage hain foot pe",
            "dark coloured bike pe bhaage",
            "cashier ko maara bhi",
            "ek aadmi zakhmi hua hai",
            "abhi bhi building mein hai",
        ],
        panic_phrases=[
            "oh my god", "jaldi please", "help", "yeh abhi ho raha hai",
            "arre arre", "bachao",
        ],
    ),
    IncidentTemplate(
        template_id="assault_in_progress",
        incident_type=IncidentType.CRIME,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.POLICE_CAR, ResourceType.AMBULANCE],
        transcript_variants=[
            "Someone is being beaten outside {location}! {detail}. The attacker is still there!",
            "Fight outside {location}, it's really bad, one person is on the ground not moving. {detail}.",
            "{panic} assault happening at {location}, victim looks seriously hurt. {detail}.",
            "Aadmi ko maar raha hai {detail} ke saath near {location}. Victim defend nahi kar pa raha.",
            "Violent fight at {location}. Khoon dikh raha hai. {detail}. Ek aadmi neeche hai.",
            "Bahut bura attack ho raha hai {location} ke bahar, attacker ruk nahi raha. {detail}.",
            "Person being attacked at {location}, multiple attackers. {detail}. Jaldi aao please.",
        ],
        detail_pool=[
            "lohe ki rod",
            "danda ya pipe",
            "haath se maar raha hai aur victim hil nahi raha",
            "koi hatyar",
            "victim ke sir se bahut khoon aa raha hai",
            "victim unconscious hai pavement pe",
            "teen attackers hain, ek victim",
        ],
        panic_phrases=[
            "hey bhagwan", "please hurry", "unhe bachao", "yeh bahut bura hai",
            "koi marega yahan",
        ],
    ),
    IncidentTemplate(
        template_id="gas_leak",
        incident_type=IncidentType.HAZARD,
        default_severity=Severity.HIGH,
        resources_needed=[ResourceType.FIRE_TRUCK, ResourceType.HAZMAT_UNIT],
        transcript_variants=[
            "Strong gas smell at {location}, it's overwhelming. {detail}. We're evacuating.",
            "{location} pe gas leak lag raha hai. {detail}. Koi bhi andar mat aana.",
            "{panic} cylinder blast ho sakta hai {location} pe, {detail}, sabko bahar kar rahe hain.",
            "Gas ki tez smell aa rahi hai near {location}. Bahut tez. {detail}.",
            "Explosion risk — LPG gas leak at {location}. {detail}. Building evacuate ho rahi hai.",
            "Gas main ke paas hissing ki awaaz aa rahi hai {location} pe aur smell bahut buri hai. {detail}.",
            "Gas company kaam kar rahi thi near {location} aur kuch leak ho gaya. {detail}.",
        ],
        detail_pool=[
            "log khansi kar rahe hain aur aankhein jal rahi hain",
            "smell aur bhi tez ho rahi hai",
            "hissing ki awaaz sun sakte hain",
            "floor evacuate kiya but baaki manzil wale still inside",
            "basement mein smell sabse tez hai",
            "gas company ko bhi call kiya hai",
            "abhi tak koi flame nahi dicha",
        ],
        panic_phrases=[
            "please jaldi", "yeh dangerous hai", "help", "abhi aao",
            "bachao", "cylinder phategi",
        ],
    ),
    IncidentTemplate(
        template_id="downed_power_line",
        incident_type=IncidentType.HAZARD,
        default_severity=Severity.MEDIUM,
        resources_needed=[ResourceType.FIRE_TRUCK],
        transcript_variants=[
            "Power line down at {location}, it's sparking on the road. {detail}.",
            "Bijli ka taar gira hua hai near {location}. {detail}. Gaadiyaan ruk gayi hain.",
            "Tree fell on power lines at {location} aur woh zameen pe aa gayi. {detail}.",
            "Live wire road pe pada hai {location} pe. {detail}. Bahut khatarnak hai.",
            "Taar aandhi mein gira near {location}. {detail}. Abhi tak koi hurt nahi.",
            "Bijli ka taar {location} pe ground pe hai, bahut sparking ho raha hai. {detail}. Log paas aa rahe hain.",
        ],
        detail_pool=[
            "abhi bhi spark kar raha hai",
            "ek gaadi ne upar se guzar di phir ruki",
            "kuch log paas ja rahe hain",
            "bijli gayi poori colony mein",
            "dono lanes block hain",
            "abhi tak koi hurt nahi",
            "paas mein chhoti ghans bhi aag pakad rahi hai",
        ],
        panic_phrases=[
            "dhyan raho", "bahut khatarnak hai", "please aao jaldi",
        ],
    ),
    IncidentTemplate(
        template_id="person_choking",
        incident_type=IncidentType.MEDICAL,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.AMBULANCE],
        transcript_variants=[
            "Someone is choking at {location}! {detail}. We tried the Heimlich, it's not working!",
            "{panic} mere bachche ko kuch fas gaya hai gale mein at {location}! {detail}! please jaldi!",
            "Person choking at {location}, turning blue, {detail}",
            "Help chahiye, mere papa ka kuch gale mein fas gaya, hum hain {location} pe. {detail}.",
            "Choking emergency at {location}, adult male, {detail}. Heimlich nahi kaam kar raha. Jaldi.",
            "Hey bhagwan {location} pe kisi ke gale mein kuch phas gaya hai, breathe nahi le pa rahe. {detail}.",
            "Medical emergency at {location}, person choking on food. {detail}.",
        ],
        detail_pool=[
            "woh neela pad raha hai",
            "hosh hai but hawa nahi aa rahi",
            "khane ka tukda fas gaya hai",
            "chhota bachcha hai, sirf 2 saal ka",
            "teen baar Heimlich kar chuke hain",
            "thoda awaaz nikal sakta hai but saans nahi",
            "behosh ho gayi",
        ],
        panic_phrases=[
            "hey bhagwan", "please please", "help karo", "jaldi",
            "neela ho raha hai", "bachao",
        ],
    ),
]

_by_id: dict[str, IncidentTemplate] = {t.template_id: t for t in _TEMPLATES}


def all_templates() -> list[IncidentTemplate]:
    """Return all registered incident templates."""
    return list(_TEMPLATES)


def get_template(template_id: str) -> IncidentTemplate:
    """Return the template with the given ID.

    Raises:
        KeyError: If no template with that ID exists.
    """
    if template_id not in _by_id:
        valid = ", ".join(sorted(_by_id))
        raise KeyError(f"Unknown template_id '{template_id}'. Valid: {valid}")
    return _by_id[template_id]
