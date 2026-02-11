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
    BrightAcoustic = GMEntry(2, "BrightAcoustic", "Piano")
    ElectricGrand = GMEntry(3, "ElectricGrand", "Piano")
    HonkyTonk = GMEntry(4, "HonkyTonk", "Piano")
    ElectricPiano1 = GMEntry(5, "ElectricPiano1", "Piano")
    ElectricPiano2 = GMEntry(6, "ElectricPiano2", "Piano")
    Harpsichord = GMEntry(7, "Harpsichord", "Piano")
    Clavinet = GMEntry(8, "Clavinet", "Piano")

    # Chromatic Percussion
    Celesta = GMEntry(9, "Celesta", "Chromatic Percussion")
    Glockenspiel = GMEntry(10, "Glockenspiel", "Chromatic Percussion")
    MusicBox = GMEntry(11, "MusicBox", "Chromatic Percussion")
    Vibraphone = GMEntry(12, "Vibraphone", "Chromatic Percussion")
    Marimba = GMEntry(13, "Marimba", "Chromatic Percussion")
    Xylophone = GMEntry(14, "Xylophone", "Chromatic Percussion")
    TubularBells = GMEntry(15, "TubularBells", "Chromatic Percussion")
    Dulcimer = GMEntry(16, "Dulcimer", "Chromatic Percussion")

    # Organ
    DrawbarOrgan = GMEntry(17, "DrawbarOrgan", "Organ")
    PercussiveOrgan = GMEntry(18, "PercussiveOrgan", "Organ")
    RockOrgan = GMEntry(19, "RockOrgan", "Organ")
    ChurchOrgan = GMEntry(20, "ChurchOrgan", "Organ")
    ReedOrgan = GMEntry(21, "ReedOrgan", "Organ")
    Accordian = GMEntry(22, "Accordian", "Organ")
    Harmonica = GMEntry(23, "Harmonica", "Organ")
    TangoAccordian = GMEntry(24, "TangoAccordian", "Organ")

    # Guitar
    NylonGuitar = GMEntry(25, "NylonGuitar", "Guitar")
    SteelGuitar = GMEntry(26, "SteelGuitar", "Guitar")
    JazzGuitar = GMEntry(27, "JazzGuitar", "Guitar")
    CleanGuitar = GMEntry(28, "CleanGuitar", "Guitar")
    MutedGuitar = GMEntry(29, "MutedGuitar", "Guitar")
    OverdrivenGuitar = GMEntry(30, "OverdrivenGuitar", "Guitar")
    DistortionGuitar = GMEntry(31, "DistortionGuitar", "Guitar")
    GuitarHarmonics = GMEntry(32, "GuitarHarmonics", "Guitar")

    # Bass
    AcousticBass = GMEntry(33, "AcousticBass", "Bass")
    FingerBass = GMEntry(34, "FingerBass", "Bass")
    PickBass = GMEntry(35, "PickBass", "Bass")
    FretlessBass = GMEntry(36, "FretlessBass", "Bass")
    SlapBass1 = GMEntry(37, "SlapBass1", "Bass")
    SlapBass2 = GMEntry(38, "SlapBass2", "Bass")
    SynthBass1 = GMEntry(39, "SynthBass1", "Bass")
    SythBass2 = GMEntry(40, "SythBass2", "Bass")

    # Strings
    Violin = GMEntry(41, "Violin", "Strings")
    Viola = GMEntry(42, "Viola", "Strings")
    Cello = GMEntry(43, "Cello", "Strings")
    Contrabass = GMEntry(44, "Contrabass", "Strings")
    TremoloStrings = GMEntry(45, "TremoloStrings", "Strings")
    PizzicatoStrings = GMEntry(46, "PizzicatoStrings", "Strings")
    OrchestralStrings = GMEntry(47, "OrchestralStrings", "Strings")
    Timpani = GMEntry(48, "Timpani", "Strings")  # Why is this in strings

    # Ensemble
    StringEnsemble1 = GMEntry(49, "StringEnsemble1", "Ensemble")
    StringEnsemble2 = GMEntry(50, "StringEnsemble2", "Ensemble")
    SynthStrings1 = GMEntry(51, "SynthStrings1", "Ensemble")
    SynthStrings2 = GMEntry(52, "SynthStrings2", "Ensemble")
    ChoirAahs = GMEntry(53, "ChoirAahs", "Ensemble")
    VoiceOohs = GMEntry(54, "VoiceOohs", "Ensemble")
    SynthVoice = GMEntry(55, "SynthVoice", "Ensemble")
    OrchestraHit = GMEntry(56, "OrchestraHit", "Ensemble")

    # Brass
    Trumpet = GMEntry(57, "Trumpet", "Brass")
    Trombone = GMEntry(58, "Trombone", "Brass")
    Tuba = GMEntry(59, "Tuba", "Brass")
    MutedTrumpet = GMEntry(60, "MutedTrumpet", "Brass")
    FrenchHorn = GMEntry(61, "FrenchHorn", "Brass")
    BrassSection = GMEntry(62, "BrassSection", "Brass")
    SynthBrass1 = GMEntry(63, "SynthBrass1", "Brass")
    SynthBrass2 = GMEntry(64, "SynthBrass2", "Brass")

    # Reed
    SopranoSax = GMEntry(65, "SopranoSax", "Reed")
    AltoSax = GMEntry(66, "AltoSax", "Reed")
    TenorSax = GMEntry(67, "TenorSax", "Reed")
    BaritoneSax = GMEntry(68, "BaritoneSax", "Reed")
    Oboe = GMEntry(69, "Oboe", "Reed")
    EnglishHorn = GMEntry(70, "EnglishHorn", "Reed")
    Bassoon = GMEntry(71, "Bassoon", "Reed")
    Clarinet = GMEntry(72, "Clarinet", "Reed")

    # Pipe
    Piccolo = GMEntry(73, "Piccolo", "Pipe")
    Flute = GMEntry(74, "Flute", "Pipe")
    Recorder = GMEntry(75, "Recorder", "Pipe")
    PanFlute = GMEntry(76, "PanFlute", "Pipe")
    BlownBottle = GMEntry(77, "BlownBottle", "Pipe")
    Shakuhachi = GMEntry(78, "Shakuhachi", "Pipe")  # ???
    Whistle = GMEntry(79, "Whistle", "Pipe")
    Ocarina = GMEntry(80, "Ocarina", "Pipe")

    # Synth Lead
    SquareLead = GMEntry(81, "SquareLead", "Synth Lead")
    SawLead = GMEntry(82, "SawLead", "Synth Lead")
    CalliopeLead = GMEntry(83, "CalliopeLead", "Synth Lead")
    ChifferLead = GMEntry(84, "ChifferLead", "Synth Lead")
    CharangLead = GMEntry(85, "CharangLead", "Synth Lead")
    VoiceLead = GMEntry(86, "VoiceLead", "Synth Lead")
    FifthsLea = GMEntry(87, "FifthsLea", "Synth Lead")
    BassPlusLead = GMEntry(88, "BassPlusLead", "Synth Lead")

    # Synth Pad
    NewAgePad = GMEntry(89, "NewAgePad", "Synth Pad")
    WarmPad = GMEntry(90, "WarmPad", "Synth Pad")
    PolySynthPad = GMEntry(91, "PolySynthPad", "Synth Pad")
    ChoirPad = GMEntry(92, "ChoirPad", "Synth Pad")
    BowedPad = GMEntry(93, "BowedPad", "Synth Pad")
    MetallicPad = GMEntry(94, "MetallicPad", "Synth Pad")
    HaloPad = GMEntry(95, "HaloPad", "Synth Pad")
    SweepPad = GMEntry(96, "SweepPad", "Synth Pad")

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
    TinkleBell = GMEntry(113, "TinkleBell", "Percussive")
    Agogo = GMEntry(114, "Agogo", "Percussive")
    SteelDrums = GMEntry(115, "SteelDrums", "Percussive")
    Woodblock = GMEntry(116, "Woodblock", "Percussive")
    TaikoDrum = GMEntry(117, "TaikoDrum", "Percussive")
    MelodicTom = GMEntry(118, "MelodicTom", "Percussive")
    SynthDrum = GMEntry(119, "SynthDrum", "Percussive")
    ReverseCymbal = GMEntry(120, "ReverseCymbal", "Percussive")

    # Sound Effects
    GuitarFretNoise = GMEntry(121, "GuitarFretNoise", "Sound Effects")
    BreathNoise = GMEntry(122, "BreathNoise", "Sound Effects")
    Seashore = GMEntry(123, "Seashore", "Sound Effects")
    BirdTweet = GMEntry(124, "BirdTweet", "Sound Effects")
    TelephoneRing = GMEntry(125, "TelephoneRing", "Sound Effects")
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
    SoundEffects = GMEntry(57, "SoundEffects", "Kits")
