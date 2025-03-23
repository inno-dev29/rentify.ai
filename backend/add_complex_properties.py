#!/usr/bin/env python
import os
import django
import random
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_platform.settings')
django.setup()

from properties.models import Property, Amenity
from users.models import User

def get_or_create_amenities():
    """Create a comprehensive list of amenities for properties"""
    amenities = {
        # Basic amenities
        'wifi': 'WiFi',
        'kitchen': 'Full kitchen',
        'washer': 'Washer',
        'dryer': 'Dryer',
        'air_conditioning': 'Air conditioning',
        'heating': 'Heating',
        'dedicated_workspace': 'Dedicated workspace',
        'tv': 'TV',
        'iron': 'Iron',
        'hangers': 'Hangers',
        'essentials': 'Essentials (towels, bed sheets, soap, toilet paper)',
        
        # Bathroom
        'hot_water': 'Hot water',
        'bidet': 'Bidet',
        'shower_gel': 'Shower gel',
        'shampoo': 'Shampoo',
        'hair_dryer': 'Hair dryer',
        
        # Security
        'smoke_alarm': 'Smoke alarm',
        'carbon_monoxide_alarm': 'Carbon monoxide alarm',
        'fire_extinguisher': 'Fire extinguisher',
        'first_aid_kit': 'First aid kit',
        'security_cameras': 'Security cameras',
        'keypad_lock': 'Keypad lock',
        
        # Luxury
        'pool': 'Pool',
        'hot_tub': 'Hot tub',
        'bbq_grill': 'BBQ grill',
        'fireplace': 'Fireplace',
        'indoor_fireplace': 'Indoor fireplace',
        'sauna': 'Sauna',
        'gym': 'Gym',
        'ocean_view': 'Ocean view',
        'beach_access': 'Beach access',
        'lake_access': 'Lake access',
        'ski_in_out': 'Ski-in/Ski-out',
        'grand_piano': 'Grand piano',
        'wine_cellar': 'Wine cellar',
        'private_theater': 'Private theater',
        
        # Work
        'printer': 'Printer',
        'monitor': 'External monitor',
        'video_conferencing_equipment': 'Video conferencing equipment',
        'high_speed_internet': 'High-speed internet (100+ Mbps)',
        
        # Accessibility
        'step_free_entrance': 'Step-free entrance',
        'wide_doorway': 'Wide doorway',
        'wide_hallway': 'Wide hallway',
        'accessible_bathroom': 'Accessible bathroom',
        'shower_chair': 'Shower chair',
        'ceiling_hoist': 'Ceiling hoist',
        
        # Family
        "childrens_books_and_toys": "Children's books and toys",
        "childrens_dinnerware": "Children's dinnerware",
        'crib': 'Crib',
        'high_chair': 'High chair',
        'baby_bath': 'Baby bath',
        'changing_table': 'Changing table',
        'game_console': 'Game console',
        'board_games': 'Board games',
        
        # Outdoor
        'patio_or_balcony': 'Patio or balcony',
        'garden': 'Garden',
        'outdoor_furniture': 'Outdoor furniture',
        'outdoor_dining_area': 'Outdoor dining area',
        'hammock': 'Hammock',
        'beach_essentials': 'Beach essentials',
        'bikes': 'Bikes',
        'kayak': 'Kayak',
        'hiking_trails': 'Hiking trails nearby',
        
        # Miscellaneous
        'breakfast': 'Breakfast',
        'ev_charger': 'EV charger',
        'sound_system': 'Sound system',
        'record_player': 'Record player',
        'piano': 'Piano',
        'art_supplies': 'Art supplies',
        'telescope': 'Telescope',
        'books': 'Books and reading material',
        'luggage_dropoff': 'Luggage dropoff allowed',
        'long_term_stays': 'Long term stays allowed',
        'self_check_in': 'Self check-in',
    }
    
    created_amenities = {}
    for key, name in amenities.items():
        amenity, created = Amenity.objects.get_or_create(name=name)
        created_amenities[key] = amenity
    
    return created_amenities

def add_complex_properties():
    """Add complex property listings with rich descriptions to challenge Claude"""
    # Get admin user for property ownership
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No admin user found. Please create an admin user first.")
        return
    
    # Get or create amenities
    amenities_dict = get_or_create_amenities()
    
    # Property 1: Sustainable Treehouse
    treehouse = Property.objects.create(
        title="Sustainable Treehouse Eco-Retreat",
        description="""Nestled 30 feet above the forest floor, this architectural marvel is a testament to sustainable luxury. Built entirely from reclaimed materials and powered by solar panels, our treehouse offers a carbon-neutral escape without sacrificing comfort.

The wraparound deck provides 360-degree views of the ancient forest, with glimpses of local wildlife at dawn and dusk. Inside, the open-concept living space features floor-to-ceiling windows, a handcrafted king bed suspended from natural timber beams, and a living wall of native plants that naturally purify the air.

The kitchenette is equipped with energy-efficient appliances and stocked with local, organic provisions. The bathroom showcases our rainwater collection system and composting toilet, demonstrating how luxury and environmental consciousness can coexist beautifully.

At night, stargaze through the skylight above your bed or use the provided telescope on the private observation platform. Fall asleep to the gentle sounds of the forest and wake to dappled sunlight filtering through the canopy.

This is more than accommodation—it's an immersive experience in harmonious living with nature, ideal for those seeking rejuvenation, romance, or creative inspiration.""",
        property_type=Property.PropertyType.CABIN,
        bedroom_count=1,
        bathroom_count=Decimal('1.0'),
        max_guests=2,
        base_price=Decimal('275.00'),
        cleaning_fee=Decimal('75.00'),
        leaser=admin_user,
        address_line1="123 Forest Path",
        city="Olympia",
        state="Washington",
        postal_code="98502",
        country="United States",
        status=Property.ListingStatus.ACTIVE
    )
    
    # Add amenities to treehouse
    treehouse_amenities = [
        'wifi', 'air_conditioning', 'heating', 'tv', 'essentials', 
        'hot_water', 'shower_gel', 'shampoo', 'hair_dryer',
        'smoke_alarm', 'carbon_monoxide_alarm', 'fire_extinguisher', 'first_aid_kit',
        'indoor_fireplace', 'telescope',
        'step_free_entrance',
        'patio_or_balcony', 'outdoor_furniture', 'hiking_trails',
        'breakfast', 'books', 'self_check_in'
    ]
    for amenity_key in treehouse_amenities:
        treehouse.amenities.add(amenities_dict[amenity_key])
    
    # Property 2: Industrial Loft
    loft = Property.objects.create(
        title="Converted Industrial Loft with Art Gallery",
        description="""Once a textile factory from the 1920s, this expansive loft has been transformed into a dynamic living space that honors its industrial heritage while embracing contemporary design. Original brick walls, exposed pipes, and concrete floors are complemented by museum-quality lighting, mobile partitions, and statement furniture pieces from local designers.

The heart of the space is the 1,500 sq ft open-concept living area with 20-foot ceilings and massive factory windows that flood the space with natural light. The bedroom is housed in a custom-built mezzanine overlooking the main space, accessible via a floating staircase crafted from reclaimed factory machinery.

The kitchen features a 12-foot island made from salvaged bowling alley wood, professional-grade appliances, and an impressive collection of cooking implements that would satisfy any chef. The bathroom is a spa-like retreat with a rainfall shower, Japanese soaking tub, and heated concrete floors.

What truly sets this property apart is the integrated gallery space, where we showcase rotating exhibitions of emerging artists. Guests are invited to opening events during their stay and may even have the opportunity to meet the artists in residence who occasionally work in the attached studio space.

Located in the heart of the arts district, you're steps away from galleries, performance venues, experimental restaurants, and boutique shops. This is an inspiring space for creative professionals, art enthusiasts, or anyone looking to experience urban living through a cultural lens.""",
        property_type=Property.PropertyType.APARTMENT,
        bedroom_count=1,
        bathroom_count=Decimal('1.5'),
        max_guests=4,
        base_price=Decimal('350.00'),
        cleaning_fee=Decimal('100.00'),
        leaser=admin_user,
        address_line1="456 Arts District Boulevard",
        city="Chicago",
        state="Illinois",
        postal_code="60642",
        country="United States",
        status=Property.ListingStatus.ACTIVE
    )
    
    # Add amenities to loft
    loft_amenities = [
        'wifi', 'kitchen', 'washer', 'dryer', 'air_conditioning', 'heating', 
        'dedicated_workspace', 'tv', 'iron', 'hangers', 'essentials',
        'hot_water', 'bidet', 'shower_gel', 'shampoo', 'hair_dryer',
        'smoke_alarm', 'carbon_monoxide_alarm', 'fire_extinguisher', 'first_aid_kit',
        'printer', 'monitor', 'high_speed_internet',
        'board_games',
        'sound_system', 'record_player', 'piano', 'art_supplies', 'books',
        'self_check_in', 'long_term_stays'
    ]
    for amenity_key in loft_amenities:
        loft.amenities.add(amenities_dict[amenity_key])
    
    # Property 3: Ancient Stone Farmhouse
    farmhouse = Property.objects.create(
        title="Ancient Stone Farmhouse with Vineyard",
        description="""Dating back to the 16th century, this meticulously restored stone farmhouse sits on 15 acres of working vineyard and olive groves in the heart of wine country. The renovation has preserved the soul of this historic property while introducing modern amenities with subtle finesse.

The two-foot-thick stone walls keep the interior cool in summer and warm in winter, complemented by underfloor heating and a central fireplace that serves both the living room and kitchen. Original wood beams, terra cotta floors, and arched doorways speak to the property's heritage, while the kitchen has been updated with professional-grade equipment that would please any culinary enthusiast.

Each of the three bedrooms has its own character: the master features a king-sized canopy bed and en-suite bathroom with a clawfoot tub; the second offers twin beds that can convert to a king and access to a private terrace; the third, located in the former hayloft, provides a cozy retreat with exposed beams and a writing desk overlooking the vineyard.

The outdoor spaces are equally compelling: a stone-paved courtyard with a 200-year-old olive tree, an infinity pool that seems to spill into the vineyard, and multiple dining areas for enjoying meals at different times of day. The covered outdoor kitchen with a wood-fired oven is perfect for pizza nights using ingredients from our vegetable garden.

Guests are invited to participate in seasonal activities, from grape harvesting and wine-making in the fall to olive picking and pressing in late autumn. Our caretaker, a local whose family has tended these lands for generations, offers private tours and tasting sessions, sharing stories that bring the history of the region to life.

This is an immersive experience in rural living, ideal for families or small groups seeking authenticity, tranquility, and connection to land and tradition.""",
        property_type=Property.PropertyType.HOUSE,
        bedroom_count=3,
        bathroom_count=Decimal('2.5'),
        max_guests=6,
        base_price=Decimal('450.00'),
        cleaning_fee=Decimal('150.00'),
        leaser=admin_user,
        address_line1="Strada Provinciale 21",
        city="Montalcino",
        state="Tuscany",
        postal_code="53024",
        country="Italy",
        status=Property.ListingStatus.ACTIVE
    )
    
    # Add amenities to farmhouse
    farmhouse_amenities = [
        'wifi', 'kitchen', 'washer', 'dryer', 'air_conditioning', 'heating',
        'tv', 'iron', 'hangers', 'essentials',
        'hot_water', 'shower_gel', 'shampoo', 'hair_dryer',
        'smoke_alarm', 'carbon_monoxide_alarm', 'fire_extinguisher', 'first_aid_kit',
        'pool', 'bbq_grill', 'fireplace', 'indoor_fireplace', 'wine_cellar',
        'crib', 'high_chair',
        'patio_or_balcony', 'garden', 'outdoor_furniture', 'outdoor_dining_area',
        'breakfast', 'books', 'long_term_stays'
    ]
    for amenity_key in farmhouse_amenities:
        farmhouse.amenities.add(amenities_dict[amenity_key])
    
    # Property 4: Floating Houseboat
    houseboat = Property.objects.create(
        title="Floating Minimalist Houseboat with Japanese Influence",
        description="""Experience waterfront living reimagined through the lens of Japanese minimalism on this architecturally significant houseboat. Custom-built by a renowned naval architect and a wabi-sabi design master, this floating home achieves perfect harmony between water, light, and space.

The 800-square-foot interior feels surprisingly spacious thanks to thoughtful design elements: retracting glass walls that open the living area to the surrounding deck, built-in furniture that eliminates visual clutter, and strategic skylights that track the sun's movement throughout the day. The materials palette is intentionally limited to cedar, paper, stone, and steel—all chosen to weather beautifully with time and elements.

The main living space transforms throughout the day: a meditation area in the morning as sunlight streams across the tatami flooring; a convenient workspace during the day with uninterrupted views inspiring creativity; and an intimate dining space in the evening, with the custom table rising from beneath the floor.

The sleeping quarters feature a traditional Japanese platform bed with organic cotton bedding and shoji screens that can divide the space for privacy or open it to harbor views. The bathroom incorporates a deep wooden soaking tub and a shower that appears to cascade directly into the water below through a cleverly designed glass floor.

The wraparound exterior deck doubles your living space in fair weather, with a covered area for enjoying the surroundings even during gentle rain. A small rowboat is tethered to the side, allowing you to explore the harbor or visit nearby restaurants accessible by water.

This isn't merely accommodation but an immersive experience in mindful living and finding luxury in simplicity. The gentle rocking of the water supports deep sleep, while watching the play of reflections on the ceiling creates a natural meditative state. Perfect for solo travelers seeking tranquility, couples desiring a romantic retreat, or creatives needing uninterrupted inspiration.""",
        property_type=Property.PropertyType.OTHER,
        bedroom_count=1,
        bathroom_count=Decimal('1.0'),
        max_guests=2,
        base_price=Decimal('295.00'),
        cleaning_fee=Decimal('85.00'),
        leaser=admin_user,
        address_line1="Pier 38, Slip 12",
        city="Sausalito",
        state="California",
        postal_code="94965",
        country="United States",
        status=Property.ListingStatus.ACTIVE
    )
    
    # Add amenities to houseboat
    houseboat_amenities = [
        'wifi', 'kitchen', 'air_conditioning', 'heating', 'dedicated_workspace',
        'tv', 'essentials',
        'hot_water', 'shower_gel', 'shampoo',
        'smoke_alarm', 'carbon_monoxide_alarm', 'fire_extinguisher', 'first_aid_kit',
        'ocean_view', 'beach_access',
        'high_speed_internet',
        'outdoor_furniture',
        'books', 'self_check_in'
    ]
    for amenity_key in houseboat_amenities:
        houseboat.amenities.add(amenities_dict[amenity_key])
    
    # Property 5: Desert Oasis
    desert_house = Property.objects.create(
        title="Modernist Desert Oasis with Observatory",
        description="""Perched on the edge of protected desert wilderness, this architectural statement house is a masterclass in environmental integration and celestial connection. Designed by a student of Frank Lloyd Wright, the structure emerges from the landscape as if it were a natural formation, with walls of volcanic stone and soaring windows that frame the mountain vistas like living art.

The main living pavilion is oriented to capture both sunrise over the mountains and sunset over the desert floor. The polished concrete floors incorporate a passive solar heating system, while deep overhangs protect from the midday sun. The furnishings—low-slung leather, desert-toned textiles, and sculptural cacti—complement rather than compete with the dramatic surroundings.

The kitchen merges indoor and outdoor cooking with a pass-through window to the sheltered courtyard, which features a firepit, plunge pool, and outdoor shower fed by our private well. Indigenous plantings attract hummingbirds and provide natural screening for ultimate privacy.

The primary bedroom suite occupies its own wing, with a king-sized platform bed positioned to view the stars through retractable roof panels. The en-suite bathroom is a sensory haven with a sunken stone tub, dual rain showers, and a private garden atrium.

What truly distinguishes this property is the attached observatory. Housing a research-grade 14-inch Schmidt-Cassegrain telescope and equipped with astrophotography capabilities, it offers unparalleled views of the night sky from this International Dark Sky location. Our property manager, an amateur astronomer, can arrange a private viewing session during your stay.

Days can be spent exploring hiking trails accessible directly from the property, visiting nearby hot springs, or simply watching the desert light transform the landscape from our meditation deck. As night falls, the absence of light pollution reveals a celestial display rarely experienced in our modern world.

This is a place for reconnection—with nature, with silence, with the cosmos, and perhaps with yourself. It appeals to design enthusiasts, nature lovers, and those seeking a truly unique experience beyond the ordinary luxury vacation.""",
        property_type=Property.PropertyType.HOUSE,
        bedroom_count=2,
        bathroom_count=Decimal('2.0'),
        max_guests=4,
        base_price=Decimal('425.00'),
        cleaning_fee=Decimal('150.00'),
        leaser=admin_user,
        address_line1="7890 Stargazer Road",
        city="Borrego Springs",
        state="California",
        postal_code="92004",
        country="United States",
        status=Property.ListingStatus.ACTIVE
    )
    
    # Add amenities to desert house
    desert_house_amenities = [
        'wifi', 'kitchen', 'washer', 'dryer', 'air_conditioning', 'heating',
        'dedicated_workspace', 'tv', 'iron', 'hangers', 'essentials',
        'hot_water', 'bidet', 'shower_gel', 'shampoo', 'hair_dryer',
        'smoke_alarm', 'carbon_monoxide_alarm', 'fire_extinguisher', 'first_aid_kit',
        'pool', 'bbq_grill', 'fireplace', 'indoor_fireplace',
        'telescope',
        'patio_or_balcony', 'outdoor_furniture', 'outdoor_dining_area', 'hiking_trails',
        'ev_charger', 'books', 'self_check_in'
    ]
    for amenity_key in desert_house_amenities:
        desert_house.amenities.add(amenities_dict[amenity_key])
    
    print(f"Added 5 complex properties with detailed descriptions and amenities")

if __name__ == "__main__":
    add_complex_properties() 