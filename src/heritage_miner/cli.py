"""Read-only local GEDCOM trace. Outputs private JSON; no network calls."""
import argparse
import json
from pathlib import Path
from .gedcom import paternal_line, read_gedcom

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gedcom', required=True, help='Private GEDCOM file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--root-id')
    group.add_argument('--root-name')
    parser.add_argument('--out', required=True, help='Private output JSON path')
    parser.add_argument('--max-generations', type=int, default=15)
    args = parser.parse_args()
    if not 1 <= args.max_generations <= 40: parser.error('max-generations must be 1..40')
    output = Path(args.out)
    if output.resolve() == Path(args.gedcom).resolve(): parser.error('output cannot overwrite source')
    people, families, digest = read_gedcom(args.gedcom)
    report = paternal_line(people, families, root_id=args.root_id, root_name=args.root_name,
                           max_generations=args.max_generations)
    report.update(schema_version='0.1', source_sha256=digest,
                  source_basename=Path(args.gedcom).name,
                  individual_count=len(people), family_count=len(families))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    try: output.chmod(0o600)
    except OSError: pass
    print('Local trace written. Inspect privately; do not commit the output.')

if __name__ == '__main__':
    main()
