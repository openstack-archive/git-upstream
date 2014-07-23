# git-upstream import could miss some local changes

## Problem description

If previous local changes were based off of a point before the previous import merge was complete, and were not rebased to be applied after this point before being merged, the import command will miss including these when discarding previous obsolete history.

Given a previous import like the following where previously changes B & C were replayed, and the import was merged as E. Where subsequently a change D which was proposed before the import, is merged to mainline, a subsequent run of the tool to import K will fail to include D along with B', C' & G' when discarding the assumed unnecessary merges E & F. While these should be discarded, the tool needs to check to make sure if there are dangling changes that should be included.

              D----
             /     \
         B---C---E---F---L  mainline
        /       /
       /   B'--C'           import/G
      /   /
     A---G---H---I---J---K  upstream



The tool will find the following commit path to consider:

                 E---F---L
                /
           B'--C'
          /
         G

## Implementing a fix (WiP)

With respect to the previous diagrams, the correct behaviour is to find the following set:

               D----
                    \
                 E---F---L
                /
           B'--C'
          /
         G

This requires walking the list of initial found (2nd diagram) and examining each merge commit up to the previous import to see if there is a change that shares history with the other parent. i.e. look at F and see if D contains a merge-base in common with E, an thus include. Or locate E and find any differences between E & L that should be included.

## Workaround

Waiting for a proper fix to be implemented, a workaround for this issue would be to perform the import only into a branch (usually master) which has no "pending" commit in other branches to be merged.
For gerrit this means not having pending reviews spanning across different git-upstream import command runs.
