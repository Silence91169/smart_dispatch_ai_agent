"""Template library of emergency incident archetypes for call generation."""

from dataclasses import dataclass, field

from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity


@dataclass
class IncidentTemplate:
    """A reusable emergency archetype that the generator renders into varied transcripts.

    Attributes:
        template_id: Unique identifier, e.g. ``house_fire_residential``.
        incident_type: The :class:`IncidentType` enum value.
        default_severity: Default :class:`Severity` if the rendered call doesn't imply otherwise.
        resources_needed: List of resource types to dispatch.
        transcript_variants: List of transcript shape strings with ``{location}``,
            ``{detail}``, and ``{panic}`` placeholders.
        detail_pool: Small detail strings that fill ``{detail}`` — add realism.
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
            "My house is on fire! {location}, please hurry, I don't know if everyone got out!",
            "{panic} house fire at {location}. {detail}. Send firefighters now!",
            "I can see a structure fire from the road near {location}. The smoke is black and thick, the whole roof is going.",
            "oh god my neighbor's house is burning, we're at {location}, {detail}, the flames are spreading to the trees!",
            "fire department come quick, {location}, residential house fire. I hear someone screaming inside. {detail}.",
            "huge fire at {location}, the house is fully involved. {detail}. I can feel the heat from across the street.",
        ],
        detail_pool=[
            "I can hear someone inside screaming",
            "the garage already collapsed",
            "the fire is spreading to the fence",
            "there might be kids inside",
            "a car in the driveway is starting to catch",
            "the neighbor's tree is on fire too",
            "I can't reach my roommate on the phone",
            "we got out but the dog is still inside",
        ],
        panic_phrases=[
            "oh my god", "please help us", "someone help", "oh no oh no",
            "hurry hurry", "we need help now",
        ],
    ),
    IncidentTemplate(
        template_id="apartment_fire_highrise",
        incident_type=IncidentType.FIRE,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.FIRE_TRUCK, ResourceType.AMBULANCE],
        transcript_variants=[
            "Fire in a high-rise apartment at {location}! The hallway on my floor is full of smoke, I can't see anything!",
            "{panic} there's a fire alarm going off at {location} and I can smell smoke on the 6th floor, this is real!",
            "I'm trapped on the upper floor of {location}, the stairwell is blocked by smoke. There are families up here!",
            "apartment complex fire at {location}. {detail}. Multiple floors, we need ladders.",
            "We evacuated from {location} but I think people are still inside. The fire looks like it started on the third floor. {detail}.",
            "smoke is pouring out the windows at the apartments on {location}. I can see flames on at least two floors.",
            "oh god I'm on the 8th floor of {location} and the hallway is on fire. We're barricaded in the apartment. {detail}.",
        ],
        detail_pool=[
            "the elevator is out",
            "families with children are on the upper floors",
            "someone said they smelled gas before it started",
            "one person already jumped to the fire escape",
            "the sprinklers aren't working",
            "there's an elderly woman next door who can't walk",
            "I can hear people pounding on doors upstairs",
        ],
        panic_phrases=[
            "oh my god", "please", "we're trapped", "help us please",
            "there are children here", "send everything you have",
        ],
    ),
    IncidentTemplate(
        template_id="cardiac_arrest",
        incident_type=IncidentType.MEDICAL,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.AMBULANCE],
        transcript_variants=[
            "oh my god my husband isn't breathing, please help, we're at {location}",
            "I need an ambulance NOW at {location}, {detail}, he's unresponsive!",
            "hello?? someone just collapsed near {location}, I don't think he has a pulse. {detail}.",
            "please hurry, there's a person down at {location}, not moving, lips are turning blue",
            "{panic} cardiac emergency at {location}, we're doing CPR, send help immediately",
            "my dad just fell over and he's not breathing. we're right outside {location}. {detail}. hurry please",
            "person collapsed at {location}, unconscious, no pulse, started CPR. {detail}. need AED.",
        ],
        detail_pool=[
            "we're doing CPR right now",
            "he just grabbed his chest and went down",
            "she was complaining of chest pain then collapsed",
            "he's completely unresponsive to me shaking him",
            "I don't know CPR, someone here is trying",
            "she's breathing very faintly",
            "I think he's been down for a few minutes",
        ],
        panic_phrases=[
            "oh god", "please please", "help me", "hurry he's dying",
            "I don't know what to do", "someone help",
        ],
    ),
    IncidentTemplate(
        template_id="car_accident_injury",
        incident_type=IncidentType.ACCIDENT,
        default_severity=Severity.HIGH,
        resources_needed=[ResourceType.AMBULANCE, ResourceType.POLICE_CAR],
        transcript_variants=[
            "Car accident at {location}, multiple vehicles, I can see injured people. {detail}.",
            "bad crash at {location}, someone ran a red light. {detail}. people need help.",
            "{panic} wreck at {location}, car vs car, {detail}",
            "There's been a serious accident near {location}. Someone is trapped inside one of the vehicles.",
            "multi-car accident at {location}. I see blood. {detail}. Send ambulance and police.",
            "collision at {location}, airbags deployed, at least one person is not moving. {detail}.",
            "someone drove through a red light at {location} and T-boned a sedan. {detail}. injured inside.",
        ],
        detail_pool=[
            "one person is slumped over the wheel",
            "a woman is bleeding from her head",
            "the driver tried to get out but couldn't",
            "there's a child in the back seat, crying",
            "one car is on fire, small flames under the hood",
            "the windshield is completely shattered",
            "someone is conscious but pinned",
        ],
        panic_phrases=[
            "oh no", "this is bad", "please hurry", "it's really bad",
        ],
    ),
    IncidentTemplate(
        template_id="car_accident_minor",
        incident_type=IncidentType.ACCIDENT,
        default_severity=Severity.MEDIUM,
        resources_needed=[ResourceType.POLICE_CAR],
        transcript_variants=[
            "Minor fender bender at {location}, no injuries that I can see. Two cars. {detail}.",
            "Car accident at {location}, both drivers are out and walking around. {detail}.",
            "Small crash near {location}, cars are blocking traffic but everyone seems okay.",
            "hey can you send someone to {location}? Two cars hit each other, nobody hurt but they're arguing.",
            "traffic accident at {location}, just a bumper situation. {detail}. Need a police report.",
            "cars collided at {location}, no injuries, just property damage. {detail}.",
        ],
        detail_pool=[
            "one bumper is hanging off",
            "they need help with the insurance stuff",
            "one driver looks pretty shaken up",
            "blocking one lane of traffic",
            "the cars aren't drivable",
            "both drivers are on their phones",
        ],
        panic_phrases=[
            "hi", "sorry to bother", "um",
        ],
    ),
    IncidentTemplate(
        template_id="armed_robbery",
        incident_type=IncidentType.CRIME,
        default_severity=Severity.HIGH,
        resources_needed=[ResourceType.POLICE_CAR],
        transcript_variants=[
            "Armed robbery in progress at {location}! {detail}. Send police now!",
            "Someone's robbing the place at {location}, they have a weapon! {detail}.",
            "{panic} robbery at {location}, {detail}, hurry!",
            "I just witnessed a robbery at {location}. The robber had a gun. They ran toward {detail}.",
            "robbery at {location}, suspect fled on foot. {detail}.",
            "man pulled a gun inside {location} and demanded money. {detail}. They just left.",
            "hold-up at {location}! guy with a knife, he's still inside. {detail}.",
        ],
        detail_pool=[
            "he still has the gun",
            "suspect is wearing a red hoodie",
            "two suspects, both masked",
            "they went north on foot",
            "they got into a dark sedan",
            "the cashier was pistol-whipped",
            "one person is hurt",
            "he's still in the building",
        ],
        panic_phrases=[
            "oh my god", "hurry please", "help", "this is happening right now",
        ],
    ),
    IncidentTemplate(
        template_id="assault_in_progress",
        incident_type=IncidentType.CRIME,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.POLICE_CAR, ResourceType.AMBULANCE],
        transcript_variants=[
            "Someone is being beaten outside {location}! {detail}. The attacker is still there!",
            "fight outside {location}, it's really bad, one person is on the ground not moving. {detail}.",
            "{panic} assault happening at {location}, victim looks seriously hurt. {detail}.",
            "Man is attacking someone with {detail} near {location}. The victim can't defend himself.",
            "violent fight at {location}. I see blood. {detail}. One person is down.",
            "brutal attack going on right outside {location}, the attacker won't stop. {detail}.",
            "person getting jumped at {location}. multiple attackers. {detail}. please hurry.",
        ],
        detail_pool=[
            "a metal pipe",
            "a baseball bat",
            "his fists, and the victim isn't moving",
            "some kind of weapon",
            "the victim is bleeding badly from the head",
            "victim unconscious on the pavement",
            "three attackers, one victim",
        ],
        panic_phrases=[
            "oh god", "please hurry", "help them", "this is really bad",
            "someone is going to die",
        ],
    ),
    IncidentTemplate(
        template_id="gas_leak",
        incident_type=IncidentType.HAZARD,
        default_severity=Severity.HIGH,
        resources_needed=[ResourceType.FIRE_TRUCK, ResourceType.HAZMAT_UNIT],
        transcript_variants=[
            "Strong gas smell at {location}, it's overwhelming. {detail}. We're evacuating.",
            "I think there's a gas leak at {location}. {detail}. Nobody go near it.",
            "{panic} gas leak at {location}, {detail}, everyone is leaving the building.",
            "smell natural gas near {location}. Really strong. {detail}.",
            "explosion risk — gas leak at {location}. {detail}. The building is being evacuated.",
            "I can hear hissing near the gas main at {location} and it smells terrible. {detail}.",
            "gas company was doing work near {location} and something is leaking. {detail}.",
        ],
        detail_pool=[
            "people are coughing and their eyes are watering",
            "the smell is getting stronger, not weaker",
            "I can hear the gas hissing",
            "we evacuated the floor but people are still in the building",
            "the basement smells the strongest",
            "someone already called the gas company but I'm calling 911 too",
            "no flames visible yet",
        ],
        panic_phrases=[
            "please hurry", "this is dangerous", "help", "we need help now",
        ],
    ),
    IncidentTemplate(
        template_id="downed_power_line",
        incident_type=IncidentType.HAZARD,
        default_severity=Severity.MEDIUM,
        resources_needed=[ResourceType.FIRE_TRUCK],
        transcript_variants=[
            "Power line down at {location}, it's sparking on the road. {detail}.",
            "Downed electrical wire near {location}. {detail}. Cars are stopping.",
            "tree fell on power lines at {location} and pulled them to the ground. {detail}.",
            "live wire in the road at {location}. {detail}. It's dangerous.",
            "wire came down in the wind near {location}. {detail}. Nobody is hurt yet.",
            "power line is on the ground at {location}, sparking badly. {detail}. People are standing too close.",
        ],
        detail_pool=[
            "it's still sparking",
            "one car drove over it before stopping",
            "there are people walking toward it",
            "the street lights are out",
            "it's blocking both lanes",
            "nobody is hurt yet",
            "a small grass fire started near it",
        ],
        panic_phrases=[
            "careful", "it's really dangerous", "please come quick",
        ],
    ),
    IncidentTemplate(
        template_id="person_choking",
        incident_type=IncidentType.MEDICAL,
        default_severity=Severity.CRITICAL,
        resources_needed=[ResourceType.AMBULANCE],
        transcript_variants=[
            "someone is choking at {location}! {detail}. We tried the Heimlich, it's not working!",
            "{panic} my child is choking at {location}! {detail}! please hurry!",
            "person choking at {location}, turning blue, {detail}",
            "I need help, my father is choking, we're at {location}. {detail}. He can't breathe.",
            "choking emergency at {location}, adult male, {detail}. Heimlich not working. hurry.",
            "oh god someone swallowed something at {location}, they can't breathe, lips turning blue. {detail}.",
            "medical emergency at {location}, person choking on food. {detail}. not breathing well.",
        ],
        detail_pool=[
            "she's turning blue",
            "he's conscious but can't get air",
            "a piece of food is stuck",
            "she's a toddler, only 2 years old",
            "we did Heimlich three times",
            "he can make a little noise but no real breaths",
            "she passed out",
        ],
        panic_phrases=[
            "oh my god", "please please", "help us", "hurry",
            "she's turning blue", "oh god",
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
