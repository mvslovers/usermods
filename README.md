# usermods

User modifications (`++USERMOD`) to IBM elements of MVS 3.8j, made by the
mvslovers projects. Each one is an SMP usermod against the owning IBM FMID,
never a function of its own, and carries an id from the `ZMG` series.

This repository held the usermods that serve more than one product, and the
register of every `ZMG` id. A usermod that serves exactly one product lives
next to that product and is listed here with a link.

**This repository is being archived.** Its only usermod, `ZMG0003`, is
superseded by the rework of `ZP60038` of 2026-11-06 (below), and the register
of the `ZMG` ids moves to the maintainers' workspace, which is not public.
`ZMG0001` and `ZMG0002` stay documented next to their product (links in the
register). The sources, tests and measurements of `ZMG0003` remain readable
here; nothing in this repository changes after the archive.

## Register

| Usermod | What it does | IBM elements | Requisites | Lives in | Status |
|---|---|---|---|---|---|
| `ZMG0001` | BREXX/370 in TSO: `EXEC`, `%name` and `name` run an exec through BREXX/370 when its first line is `/* REXX */` | `IKJCT430` (EXEC), new `IKJCT437` | `PRE(UY16532)` | [mvslovers/brexx370](https://github.com/mvslovers/brexx370/tree/master/tso) | released with BREXX/370 3.0.0 |
| `ZMG0002` | REKX/370 (rekx370) in TSO: the same for REKX/370 | `IKJEFT01`, `IKJCT430` (EXEC), new `IKJEFTRX`, `IKJCT437` | `PRE(UY16532,UY13431)` | [mvslovers/rekx370](https://github.com/mvslovers/rekx370/tree/main/tso) | not yet released |
| `ZMG0003` | `IKJCT441` for REXX: the variable access routine serves the variables of a running REXX exec as well as CLIST variables, so ISPF dialog variables work from REXX | `IKJCT441` in `IKJPTGT` | `PRE(ZP60038)` | [this repository](zmg0003/) | **superseded** by the rework of `ZP60038` of 2026-11-06 (below); released with BREXX/370 3.1.0; the id stays spent |

**`ZMG0001` and `ZMG0002` exclude each other**: both change the TSO `EXEC`
command. `ZMG0003` changes none of their elements and can be installed with
either of them.

**`ZMG0003` is superseded by the rework of `ZP60038` of 2026-11-06**
(`++USERMOD(ZP60038) REWORK(20261106)`). Rob Prins took the module of `ZMG0003`
into `ZP60038` itself. The rework is his package
[zp60038.zip](https://prince-webdesign.nl/images/downloads/zp60038.zip)
(sha256 `d0120eaf75f992a17629b6c7bcb428b8ad5376672df8a4e225cea01bd655b626`),
with its own install job and cover letter; TK5 Update 6 comes with it. A
system with the rework does not need `ZMG0003`, and a new install takes the
rework. Measured: the rework's `APPLY` ends with RC 12 (`HMA3190`) while
`ZMG0003` is applied. The id `ZMG0003` is spent and is not reused. What was
measured, and how to tell the two apart, is in
[`zmg0003/README.md`](zmg0003/README.md).

**`ZMG0003` was reserved until 2026-11-05 for a usermod running both REXX side
by side, which was never built or shipped, and this usermod was called
`ZMG0004` during development.** The texts of BREXX/370 3.0.0 still give
`ZMG0003` the old meaning and its check job `ZMG01CK` lists it as one that must
not be installed; for the `IKJCT441` usermod that does not apply. Should a
side-by-side usermod come after all, it gets a new id. `ZMG0004` is spent.

## Conventions

- **Ids.** `ZMG` followed by four digits, counted up here. An id is spent
  once, also when the usermod is withdrawn. `ZP…` is Greg Price's series;
  `A`, `U`, `E`, `F`, `H` and `J` belong to IBM.
- **Owning FMID.** `++VER(Z038) FMID(…)` names the IBM function that owns the
  changed elements (for TSO: `EBB1102`).
- **Source form.** A usermod is shipped as source and assembled with IFOX00 on
  the target system against its own `SYS1.MACLIB` and `SYS1.AMODGEN`, as one
  library `USERMOD.<name>`: the cover letter with the MCS, the sources, and the
  jobs to check, back up, install, verify and remove it.
- **Usermods are never accepted, their requisites are.** A usermod stays removable with
  `RESTORE`, and `RESTORE` refuses it while a sysmod it requires is only applied. So its
  cover letter says what to accept before the install.
- **The `IRX*` namespace belongs to REKX/370.** No usermod here ships a
  module, alias or entry point named `IRX*`, and none loads or links one by
  name. `ZMG0003` reaches the REXX variable interface only through the
  environment block of the running exec.
