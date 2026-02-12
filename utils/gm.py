from dataclasses import dataclass


@dataclass
class GMEntry:
    value: int
    name: str
    category: str


class GMPrograms:
    # I manually copied this lol!
    # https://www.cs.cmu.edu/~music/cmp/archives/cmsip/readings/GMSpecs_Patches.htm

    # Piano
    AcousticGrand = GMEntry(1, "Acoustic Grand", "Piano")
    BrightAcoustic = GMEntry(2, "Bright Acoustic", "Piano")
    ElectricGrand = GMEntry(3, "Electric Grand", "Piano")
    HonkyTonk = GMEntry(4, "Honky Tonk", "Piano")
    ElectricPiano1 = GMEntry(5, "Electric Piano 1", "Piano")
    ElectricPiano2 = GMEntry(6, "Electric Piano 2", "Piano")
    Harpsichord = GMEntry(7, "Harpsichord", "Piano")
    Clavinet = GMEntry(8, "Clavinet", "Piano")

    # Chromatic Percussion
    Celesta = GMEntry(9, "Celesta", "Chromatic Percussion")
    Glockenspiel = GMEntry(10, "Glockenspiel", "Chromatic Percussion")
    MusicBox = GMEntry(11, "Music Box", "Chromatic Percussion")
    Vibraphone = GMEntry(12, "Vibraphone", "Chromatic Percussion")
    Marimba = GMEntry(13, "Marimba", "Chromatic Percussion")
    Xylophone = GMEntry(14, "Xylophone", "Chromatic Percussion")
    TubularBells = GMEntry(15, "Tubular Bells", "Chromatic Percussion")
    Dulcimer = GMEntry(16, "Dulcimer", "Chromatic Percussion")

    # Organ
    DrawbarOrgan = GMEntry(17, "Drawbar Organ", "Organ")
    PercussiveOrgan = GMEntry(18, "Percussive Organ", "Organ")
    RockOrgan = GMEntry(19, "Rock Organ", "Organ")
    ChurchOrgan = GMEntry(20, "Church Organ", "Organ")
    ReedOrgan = GMEntry(21, "Reed Organ", "Organ")
    Accordian = GMEntry(22, "Accordian", "Organ")
    Harmonica = GMEntry(23, "Harmonica", "Organ")
    TangoAccordian = GMEntry(24, "Tango Accordian", "Organ")

    # Guitar
    NylonGuitar = GMEntry(25, "Nylon Guitar", "Guitar")
    SteelGuitar = GMEntry(26, "Steel Guitar", "Guitar")
    JazzGuitar = GMEntry(27, "Jazz Guitar", "Guitar")
    CleanGuitar = GMEntry(28, "Clean Guitar", "Guitar")
    MutedGuitar = GMEntry(29, "Muted Guitar", "Guitar")
    OverdrivenGuitar = GMEntry(30, "Overdriven Guitar", "Guitar")
    DistortionGuitar = GMEntry(31, "Distortion Guitar", "Guitar")
    GuitarHarmonics = GMEntry(32, "Guitar Harmonics", "Guitar")

    # Bass
    AcousticBass = GMEntry(33, "Acoustic Bass", "Bass")
    FingerBass = GMEntry(34, "Finger Bass", "Bass")
    PickBass = GMEntry(35, "Pick Bass", "Bass")
    FretlessBass = GMEntry(36, "Fretless Bass", "Bass")
    SlapBass1 = GMEntry(37, "Slap Bass 1", "Bass")
    SlapBass2 = GMEntry(38, "Slap Bass 2", "Bass")
    SynthBass1 = GMEntry(39, "Synth Bass 1", "Bass")
    SynthBass2 = GMEntry(40, "Synth Bass 2", "Bass")

    # Strings
    Violin = GMEntry(41, "Violin", "Strings")
    Viola = GMEntry(42, "Viola", "Strings")
    Cello = GMEntry(43, "Cello", "Strings")
    Contrabass = GMEntry(44, "Contrabass", "Strings")
    TremoloStrings = GMEntry(45, "Tremolo Strings", "Strings")
    PizzicatoStrings = GMEntry(46, "Pizzicato Strings", "Strings")
    OrchestralStrings = GMEntry(47, "Orchestral Strings", "Strings")
    Timpani = GMEntry(48, "Timpani", "Strings")  # Why is this in strings

    # Ensemble
    StringEnsemble1 = GMEntry(49, "String Ensemble 1", "Ensemble")
    StringEnsemble2 = GMEntry(50, "String Ensemble 2", "Ensemble")
    SynthStrings1 = GMEntry(51, "Synth Strings 1", "Ensemble")
    SynthStrings2 = GMEntry(52, "Synth Strings 2", "Ensemble")
    ChoirAahs = GMEntry(53, "Choir Aahs", "Ensemble")
    VoiceOohs = GMEntry(54, "Voice Oohs", "Ensemble")
    SynthVoice = GMEntry(55, "Synth Voice", "Ensemble")
    OrchestraHit = GMEntry(56, "Orchestra Hit", "Ensemble")

    # Brass
    Trumpet = GMEntry(57, "Trumpet", "Brass")
    Trombone = GMEntry(58, "Trombone", "Brass")
    Tuba = GMEntry(59, "Tuba", "Brass")
    MutedTrumpet = GMEntry(60, "Muted Trumpet", "Brass")
    FrenchHorn = GMEntry(61, "French Horn", "Brass")
    BrassSection = GMEntry(62, "BrassS ection", "Brass")
    SynthBrass1 = GMEntry(63, "Synth Brass1", "Brass")
    SynthBrass2 = GMEntry(64, "Synth Brass2", "Brass")

    # Reed
    SopranoSax = GMEntry(65, "Soprano Sax", "Reed")
    AltoSax = GMEntry(66, "Alto Sax", "Reed")
    TenorSax = GMEntry(67, "Tenor Sax", "Reed")
    BaritoneSax = GMEntry(68, "Baritone Sax", "Reed")
    Oboe = GMEntry(69, "Oboe", "Reed")
    EnglishHorn = GMEntry(70, "English Horn", "Reed")
    Bassoon = GMEntry(71, "Bassoon", "Reed")
    Clarinet = GMEntry(72, "Clarinet", "Reed")

    # Pipe
    Piccolo = GMEntry(73, "Piccolo", "Pipe")
    Flute = GMEntry(74, "Flute", "Pipe")
    Recorder = GMEntry(75, "Recorder", "Pipe")
    PanFlute = GMEntry(76, "Pan Flute", "Pipe")
    BlownBottle = GMEntry(77, "Blown Bottle", "Pipe")
    Shakuhachi = GMEntry(78, "Shakuhachi", "Pipe")  # ???
    Whistle = GMEntry(79, "Whistle", "Pipe")
    Ocarina = GMEntry(80, "Ocarina", "Pipe")

    # Synth Lead
    SquareLead = GMEntry(81, "Square Lead", "Synth Lead")
    SawLead = GMEntry(82, "Saw Lead", "Synth Lead")
    CalliopeLead = GMEntry(83, "Calliope Lead", "Synth Lead")
    ChifferLead = GMEntry(84, "Chiffer Lead", "Synth Lead")
    CharangLead = GMEntry(85, "Charang Lead", "Synth Lead")
    VoiceLead = GMEntry(86, "Voice Lead", "Synth Lead")
    FifthsLead = GMEntry(87, "Fifths Lead", "Synth Lead")
    BassPlusLead = GMEntry(88, "Bass Plus Lead", "Synth Lead")

    # Synth Pad
    NewAgePad = GMEntry(89, "NewAge Pad", "Synth Pad")
    WarmPad = GMEntry(90, "Warm Pad", "Synth Pad")
    PolySynthPad = GMEntry(91, "PolySynth Pad", "Synth Pad")
    ChoirPad = GMEntry(92, "Choir Pad", "Synth Pad")
    BowedPad = GMEntry(93, "Bowed Pad", "Synth Pad")
    MetallicPad = GMEntry(94, "Metallic Pad", "Synth Pad")
    HaloPad = GMEntry(95, "Halo Pad", "Synth Pad")
    SweepPad = GMEntry(96, "Sweep Pad", "Synth Pad")

    # Synth Effects
    Rain = GMEntry(97, "Rain", "Synth Effects")
    Soundtrack = GMEntry(98, "Soundtrack", "Synth Effects")
    Crystal = GMEntry(99, "Crystal", "Synth Effects")
    Atmosphere = GMEntry(100, "Atmosphere", "Synth Effects")
    Brightness = GMEntry(101, "Brightness", "Synth Effects")
    Goblins = GMEntry(102, "Goblins", "Synth Effects")
    Echoes = GMEntry(103, "Echoes", "Synth Effects")
    SciFi = GMEntry(104, "SciFi", "Synth Effects")

    # Ethnic
    Sitar = GMEntry(105, "Sitar", "Ethnic")
    Banjo = GMEntry(106, "Banjo", "Ethnic")
    Shamisen = GMEntry(107, "Shamisen", "Ethnic")
    Koto = GMEntry(108, "Koto", "Ethnic")
    Kalimba = GMEntry(109, "Kalimba", "Ethnic")
    Bagpipe = GMEntry(110, "Bagpipe", "Ethnic")
    Fiddle = GMEntry(111, "Fiddle", "Ethnic")
    Shanai = GMEntry(112, "Shanai", "Ethnic")

    # Percussive
    TinkleBell = GMEntry(113, "Tinkle Bell", "Percussive")
    Agogo = GMEntry(114, "Agogo", "Percussive")
    SteelDrums = GMEntry(115, "Steel Drums", "Percussive")
    Woodblock = GMEntry(116, "Woodblock", "Percussive")
    TaikoDrum = GMEntry(117, "Taiko Drum", "Percussive")
    MelodicTom = GMEntry(118, "Melodic Tom", "Percussive")
    SynthDrum = GMEntry(119, "Synth Drum", "Percussive")
    ReverseCymbal = GMEntry(120, "Reverse Cymbal", "Percussive")

    # Sound Effects
    GuitarFretNoise = GMEntry(121, "Guitar Fret Noise", "Sound Effects")
    BreathNoise = GMEntry(122, "Breath Noise", "Sound Effects")
    Seashore = GMEntry(123, "Seashore", "Sound Effects")
    BirdTweet = GMEntry(124, "Tweet", "Sound Effects")
    TelephoneRing = GMEntry(125, "Telephone", "Sound Effects")
    Helicopter = GMEntry(126, "Helicopter", "Sound Effects")
    Applause = GMEntry(127, "Applause", "Sound Effects")
    Gunshot = GMEntry(128, "Gunshot", "Sound Effects")


class GMDrumKits:
    Standard = GMEntry(1, "Standard", "Kits")
    Room = GMEntry(9, "Room", "Kits")
    Power = GMEntry(17, "Power", "Kits")
    Electronic = GMEntry(25, "Electronic", "Kits")
    TR808 = GMEntry(26, "TR808", "Kits")
    Jazz = GMEntry(33, "Jazz", "Kits")
    Brush = GMEntry(41, "Brush", "Kits")
    Orchestra = GMEntry(49, "Orchestra", "Kits")
    SoundEffects = GMEntry(57, "Sound Effects", "Kits")
