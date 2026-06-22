from snippets import *

parser = create_arg_parser()
args, other_args = parser.parse_known_args()

examples = list(find_examples(args.lab, args.example))
examples.sort(key=lambda example: example.name)

exercises = list(find_exercises(args.lab))
exercises.sort(key=lambda exercise: exercise.name)

if args.example is not None:
    if not examples:
        print('No examples found')
    elif len(examples) > 1:
        print('# Multiple examples found, pick one:')
        for i, example in enumerate(examples):
            print(f'#    {i + 1})', example.name)
        choice = int(input('# > '))
        examples[choice - 1].run(*other_args)
    else:
        examples[0].run(*other_args)

if exercises:
    exercises[0].run(*other_args)
else:
    print('No exercises found')
