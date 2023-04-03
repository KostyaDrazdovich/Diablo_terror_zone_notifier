class Buttons:
    CANCEL = "Cancel"
    CLOSE = "Close"
    CURRENT = "/current"
    FAV = "/fav"
    HELP = "/help"
    NOTIFICATION_START = "/notification_start"
    NOTIFICATION_STATUS = "/notification_status"
    NOTIFICATION_STOP = "/notification_stop"
    REMOVE = "/remove"
    SELECT = "/select"
    START = "start"


class CommandsMessages:
    START = "Welcome to Diablo 2 terror zone bot notifier."
    HELP = "Hello!\nThis bot shows information about the current " \
           "Terror Zone in Diablo 2 Resurrected.\n" \
           "The information about current TZ is provided by https://d2runewizard.com\n" \
           "\n" \
           "For selecting favorite terror zones, type /select\n" \
           "For requesting info about current terror zone, type /current\n" \
           "For requesting your favorite terror zones, type /fav\n" \
           "For stop bot running, type /notification_stop\n" \
           "For start bot running, type /notification_start\n" \
           "For check current notification status, type /notification_status"
    CLOSED = "Closed"
    CURRENT_TERROR_ZONE = "Current terror zone is {}"
    FAV_USER_ZONES = "Your favorite Terror Zones:\n"
    SELECT_ZONE_TO_REMOVE = "Select Terror Zone to remove:"
    ZONE_ADDED_TO_FAV = "You added {}"
    ZONE_ALREADY_IN_FAV = "{} is already in favorite terror zones list"
    ZONE_ALREADY_REMOVED = "Invalid index for favorite terror zones list."
    ZONE_REMOVED_FROM_FAV = "You removed {} from favorite terror zones"


class InfoMessages:
    NOTIFICATIONS_ALREADY_DISABLED = "Notifications are already turned off!"
    NOTIFICATIONS_ALREADY_ENABLED = "Notifications are already turned on!"
    NOTIFICATIONS_DISABLED = "Notifications are currently disabled."
    NOTIFICATIONS_ENABLED = "Notifications are currently enabled."
    NO_SELECTED_TERROR_ZONES = "You haven't selected any favorite Terror Zones yet."
    SELECT_FAVORITE_TERROR_ZONE = "Select favorite Terror Zone:"
    SELECT_LOCATION_FOR_ACT = "Select location for {}:"


class JsonFields:
    NOTIFICATIONS_ENABLED = "notifications_enabled"
    TERROR_ZONE = "terrorZone"
    REPORTED_ZONES = "reportedZones"
    ZONES = "zones"


class Locations:
    ACT1 = "Act 1"
    ACT2 = "Act 2"
    ACT3 = "Act 3"
    ACT4 = "Act 4"
    ACT5 = "Act 5"
    ZONES = {"1.1": "Blood Moor and Den of Evil",
             "1.2": "Cold Plains and The Cave",
             "1.3": "Burial Grounds, The Crypt, and The Mausoleum",
             "1.4": "Stony Field",
             "1.5": "Dark Wood and Underground Passage",
             "1.6": "Black Marsh and The Hole",
             "1.7": "The Forgotten Tower",
             "1.8": "Jail and Barracks",
             "1.9": "Cathedral and Catacombs",
             "1.10": "The Pit",
             "1.11": "Tristram",
             "1.12": "Moo Moo Farm",
             "2.1": "Sewers",
             "2.2": "Rocky Waste and Stony Tomb",
             "2.3": "Dry Hills and Halls of the Dead",
             "2.4": "Far Oasis",
             "2.5": "Lost City, Valley of Snakes, and Claw Viper Temple",
             "2.6": "Ancient Tunnels",
             "2.7": "Arcane Sanctuary",
             "2.8": "Tal Rasha's Tombs and Tal Rasha's Chamber",
             "3.1": "Spider Forest and Spider Cavern",
             "3.2": "Great Marsh",
             "3.3": "Flayer Jungle and Flayer Dungeon",
             "3.4": "Kurast Bazaar, Ruined Temple, and Disused Fane",
             "3.5": "Travincal",
             "3.6": "Durance of Hate",
             "4.1": "Outer Steppes and Plains of Despair",
             "4.2": "River of Flame and City of the Damned",
             "4.3": "Chaos Sanctuary",
             "5.1": "Bloody Foothills, Frigid Highlands and Abaddon",
             "5.2": "Glacial Trail and Drifter Cavern",
             "5.3": "Crystalline Passage and Frozen River",
             "5.4": "Arreat Plateau and Pit of Acheron",
             "5.5": "Nihlathak's Temple, Halls of Anguish, Halls of Pain, and Halls of Vaught",
             "5.6": "Ancient's Way and Icy Cellar",
             "5.7": "Worldstone Keep, Throne of Destruction, and Worldstone Chamber"
             }
