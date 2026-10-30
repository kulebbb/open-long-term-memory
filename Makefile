AGENT ?= auto

.PHONY: setup index test check install-skills uninstall-skills

setup:
	git config core.hooksPath .githooks

index:
	python3 scripts/build_memory_index.py

test:
	python3 -m unittest discover -s tests -v

check:
	python3 -m unittest discover -s tests -v
	python3 scripts/build_memory_index.py --check
	sh -n scripts/memory-sync.sh
	sh -n scripts/install-agent-skills.sh

install-skills:
	sh scripts/install-agent-skills.sh --agent "$(AGENT)"

uninstall-skills:
	sh scripts/install-agent-skills.sh --agent "$(AGENT)" --uninstall
