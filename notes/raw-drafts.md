# Robium — Raw Draft Notes (verbatim, as dictated)

> Original notes captured 2026-07-09, unedited.

- Project name is robium.

- Robium is an **AI-agent-first robotics dev toolchain**:

- It's going to be mostly ai coding plugin / like claude plugin. Will contain skills

- I don't want to have actual working coding or generated code.. it should contain examples, helper scripts, skill files, references other then skills

- For skills, I want to have diffeernt flavors of skills related to robotics. One is robotic application archiutect skills, which can decide how to scaffold the application whic h libnraries to use, how to get them together, how to generate such a system, what data to use etc.. this is architect

- another skill would be how to get all these difernt systems together.. hwo to glue them.. it should write a good dockerized container dockerfile.. decided hwo different moduels / system will talj to each other.. etc..

- another skill would be where to find the data.. will we generate it from real scenarios , get offline datasets etc..

- abother skill would be ros usagfes.. it should have ros knowledge skill glue packages together

- another skill would be hugging face usages.. not only valid from hugging face but all these libraries might have their own plugins.. when we write skills they should also be aware of the opliugins related to that library or skills and instead of we write everything from scratch we should mostlly be able to use those plugins or skills

- Similarly, nvidia robotics ecosystem usage.. our skills should conatin how to use integrate nvidia ecossystems..

- another one would be le-robot skills

- another one would be visualization skills . we should know how to visualize best practices etc... what atre the tools for visualzaition.. also sperate skills for rviz .. rerun.. foxflobe etc..

- another skill would be simualtion sklills how to simulate corerct sensors etc.. what simualtors to use

- we should also contain good battle tested samples in those skills folders.. each in respective folders.. architect skils might use more higher lelvel scaffolding examples or docker exampels.. lower skills may caointain how theose modules are used in that context

- in general i don't want to invent any syntax.. mostly we want to contain skills natural languea + example snippets + docker files + helper scripts if we think some scripts would be very helpful and repetivielt used a lot..

- I want to be able to support both local and remote server usage. For this we should be virtual environemtn first deisng.. either through docker if we can't have full cirutal env or use pythin virtual env or uvx or uv envs.. so that we can esily repro in local vs remote.

- for mvp product i want to target two verticals one is classical robotics using ros .. mobile robot navigation.. second one is more ml focues pysical ai hand manipulation coul dbe either le robot or google robotics library or nvidia..

- mirror `huggingface/skills` (HuggingFace's real-world implementation of the Agent Skills / `SKILL.md` convention) when developoing our repository structure.. we should be skills heavy.. Research into `huggingface/skills` — the closest real-world precedent — showed HuggingFace distributes primarily as a **Claude Code / Cursor plugin marketplace alongside a CLI (`hf`)**, Investigate verymuch in deetail how hugging face skills are creted.. they follow some skill format.. use those skill format as well https://agentskills.io/home — our stucture can also contain scripts (frequently used scripts) and agents etc..

- I'll also use superpowers brainstorming before starting the project.. we'll need to format our initial draft brainstorming to be consumable by that superpower brainstormer.. and it should continue brainstorming based on our draft.

- another very important thing is that, when we develop these skills we'll probably iterate based on try .. I'll ahave another robium-applications repo where i'll try to use these robium skills to generate different applications and during this development we'll investigate how we can make our skills better more intlligenet more batttel testted.. sometimes, we'll develop some apps woihtout these skills and i'll let our skills learn from developed apps. we should have a big emphasis how we'll generated these skills. for these we should also use claudes skill generation skills as well as have read examples from other repositories.. examples of ros applications and try to come up with good skills that can be reused

- oru skills should alway try to have a good generilzaitiin as well.. shoudl contain exaple snippets, how to make customizations,. example config files.. importatn points for differnt platforms.. examples , links or refernces to samples / repos / skills / plugins or documentations from those libraries websites etc...

- I want to make this robium one stop robotics plugin when people want to develop any robotoics applciation using their agents, they should always try to enable this plugin and this roboium will help them to find the best suitable libraries/framework/tools and also logic to glue all those good patterns, practices to get siuccessfl run, also testing metgods, sample datas etc.. they will still use agents but agents will get a big burst with this plugin.. this is one of our main points..

- also we should have a test driven .... we can have sample applications we shoiuld always keep it mainted and running .. this would be robium-applications.. and tjhey should be test driven.. also our skills will use those repos / applications as samples as well
