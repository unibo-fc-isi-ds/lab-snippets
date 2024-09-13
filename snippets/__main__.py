from snippets import *


parser = create_arg_parser()
args = parser.parse_args()


examples = list(find_examples(args.lab, args.example))
examples.sort(key=lambda example: example.name)

if not examples:
    print('No examples found')
    exit(1)
elif len(examples) > 1:
    print('# Multiple examples found, pick one:')
    for i, example in enumerate(examples):
        print(f'#    {i+1})', example.name)
    choice = int(input('# > '))
    examples[choice - 1].run()
else:
    examples[0].run()
