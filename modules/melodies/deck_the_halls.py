from modules.melodies.notes import MelodyNotes

class MelodyDeckTheHalls:

    PAUSE = 0.30
    PACE = 0.800
    MELODY = [
        MelodyNotes.notes['G5'], MelodyNotes.notes['F5'], MelodyNotes.notes['E5'], MelodyNotes.notes['D5'],
        MelodyNotes.notes['C5'], MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['C5'],
        MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['F5'], MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['D5'],
        MelodyNotes.notes['C5'], MelodyNotes.notes['B4'], MelodyNotes.notes['C5'], 0,

        # MelodyNotes.notes['G5'], MelodyNotes.notes['F5'], MelodyNotes.notes['E5'], MelodyNotes.notes['D5'],
        # MelodyNotes.notes['C5'], MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['C5'],
        # MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['F5'], MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['D5'],
        # MelodyNotes.notes['C5'], MelodyNotes.notes['B4'], MelodyNotes.notes['C5'], 0,
        #
        # MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['F5'], MelodyNotes.notes['D5'],
        # MelodyNotes.notes['E5'], MelodyNotes.notes['F5'], MelodyNotes.notes['G5'], MelodyNotes.notes['D5'],
        # MelodyNotes.notes['E5'], MelodyNotes.notes['F5'], MelodyNotes.notes['G5'], MelodyNotes.notes['A5'], MelodyNotes.notes['B5'], MelodyNotes.notes['C6'],
        # MelodyNotes.notes['B5'], MelodyNotes.notes['A5'], MelodyNotes.notes['G5'], 0,
        #
        # MelodyNotes.notes['G5'], MelodyNotes.notes['F5'], MelodyNotes.notes['E5'], MelodyNotes.notes['D5'],
        # MelodyNotes.notes['C5'], MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['C5'],
        # MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['F5'], MelodyNotes.notes['D5'], MelodyNotes.notes['E5'], MelodyNotes.notes['D5'],
        # MelodyNotes.notes['C5'], MelodyNotes.notes['B4'], MelodyNotes.notes['C5'], 0,
    ]

    TEMPO = [
        2, 4, 2, 2,
        2, 2, 2, 2,
        4, 4, 4, 4, 2, 4,
        2, 2, 2, 2,

        2, 4, 2, 2,
        2, 2, 2, 2,
        4, 4, 4, 4, 2, 4,
        2, 2, 2, 2,

        2, 4, 2, 2,
        2, 4, 2, 2,
        4, 4, 2, 4, 4, 2,
        2, 2, 2, 2,

        2, 4, 2, 2,
        2, 2, 2, 2,
        4, 4, 4, 4, 2, 4,
        2, 2, 2, 2,
    ]