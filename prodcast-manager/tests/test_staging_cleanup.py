from unittest.mock import Mock
import pytest
from prodcast_manager.ssh import Remote


def remote(stage,windows=False):
    obj=Remote.__new__(Remote);obj.stage=stage;obj.windows=windows;obj.role='worker2' if windows else 'db'
    obj.command=Mock();obj.root=Mock();obj.log=Mock()
    return obj


def test_linux_cleanup_uses_agent_privileges_and_is_idempotent():
    obj=remote('/var/tmp/prodcast-manager-'+'a'*32)
    obj.cleanup();obj.cleanup()
    obj.root.assert_called_once()
    obj.command.assert_not_called()
    assert obj.stage is None


@pytest.mark.parametrize('stage',['/var/tmp','/','/var/lib/prodcast-manager','/var/tmp/prodcast-manager-'+'a'*32+'/..','/var/tmp/prodcast-manager-evil'])
def test_linux_cleanup_rejects_non_generated_targets(stage):
    obj=remote(stage)
    with pytest.raises(ValueError,match='Unsafe'):obj.cleanup()
    obj.root.assert_not_called();obj.command.assert_not_called()


@pytest.mark.parametrize('stage',['C:/ProgramData/ProdCastManager/inbox/','C:/ProdCast/Managed','C:/ProgramData/ProdCastManager/inbox/'+'b'*32+'/..'])
def test_windows_cleanup_rejects_broad_and_traversal_targets(stage):
    obj=remote(stage,True)
    with pytest.raises(ValueError,match='Unsafe'):obj.cleanup()
    obj.command.assert_not_called()


def test_failure_retains_stage_for_diagnostics():
    obj=remote('/var/tmp/prodcast-manager-'+'a'*32)
    obj.root.side_effect=RuntimeError('permission denied')
    with pytest.raises(RuntimeError):obj.cleanup()
    assert obj.stage.endswith('a'*32)
    obj.cleanup_warning(RuntimeError('failed'))
    assert 'db' in obj.log.call_args[0][0] and obj.stage in obj.log.call_args[0][0]
